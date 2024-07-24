from pathlib import Path
from typing import Union
import uuid
from database.models_v1 import DerivedContent, Enum_Derived_Content_Status
from utils.db import DerivedContentTypeMap, get_derived_content_type_uuid
from sqlalchemy import delete
import asyncio

from openai import OpenAIError

from modal_funcs import (
    make_folder_tech_doc,
    make_tech_doc,
    make_symbol_docs,
    make_toplevel_tech_docs,
)
from utils.dag import LiteNode
from utils.task import Task, TaskResult, TaskResultKind

TechDocsTask = Union["FileTechDocTask", "FolderTechDocTask", "TopLevelDocsTask"]

symbols_sem = asyncio.Semaphore(20)
tech_docs_sem = asyncio.Semaphore(20)
folder_tech_docs_sem = asyncio.Semaphore(20)
database_sem = asyncio.Semaphore(5)


class FolderTechDocTask(Task):
    def __init__(
        self,
        node: LiteNode,
        task_name: str,
        child_docs_tasks: tuple[TechDocsTask],
        codebase_name: str,
        source_content_id: uuid.UUID,
    ):
        self.node = node
        self.child_docs_tasks = child_docs_tasks
        self.codebase_name = codebase_name
        self.source_content_id = source_content_id
        super().__init__(task_name=task_name, dependencies=child_docs_tasks)

    async def run_implementation(
        self, dependent_results: dict[TechDocsTask, TaskResult]
    ) -> dict[str, any]:
        # Here, we know we have results for all the child nodes, so processing can commence.
        # We only want to use the results that were successful to prevent folder docs failures due to files that failed to process
        child_nodes_to_docs = {
            task.node: dr.result["docs"]
            for task, dr in dependent_results.items()
            if dr.state == TaskResultKind.SUCCESS
        }
        async with folder_tech_docs_sem:
            docs = await make_folder_tech_doc.remote.aio(
                codebase_name=self.codebase_name,
                node=self.node,
                child_nodes_to_docs=child_nodes_to_docs,
            )

        from sqlmodel.ext.asyncio.session import AsyncSession
        from database.db import async_engine

        async with database_sem:
            short_single_sentence_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.SHORT_SENTENCE_DESCRIPTION
            )
            short_single_paragraph_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.SHORT_PARAGRAPH_DESCRIPTION
            )
            long_descrip_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.LONG_DESCRIPTION
            )

            # Short Single Sentence
            short_sent_dc = DerivedContent(
                content_type_id=short_single_sentence_dc_id,
                source_content_id=self.source_content_id,
                content=docs["short"]["single_sentence"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Short Single Paragraph
            short_para_dc = DerivedContent(
                content_type_id=short_single_paragraph_dc_id,
                source_content_id=self.source_content_id,
                content=docs["short"]["single_paragraph"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Long File Description
            long_desc_dc = DerivedContent(
                content_type_id=long_descrip_dc_id,
                source_content_id=self.source_content_id,
                content=docs["long"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )

            async with AsyncSession(async_engine) as session:
                # TODO: we aren't deleting here. When we create embeddings, we'll want to cascade
                # delete everything related to old derived content

                del_statement = delete(DerivedContent).where(
                    DerivedContent.source_content_id == self.source_content_id,
                    DerivedContent.content_type_id.in_(
                        [
                            short_single_paragraph_dc_id,
                            short_single_sentence_dc_id,
                            long_descrip_dc_id,
                        ]
                    ),
                )
                await session.exec(del_statement)
                await session.commit()

                dc_records = [short_sent_dc, short_para_dc, long_desc_dc]
                session.add_all(dc_records)
                await session.commit()

        return {"docs": docs}

    def hashable_attrs(self) -> tuple:
        return (self.task_name, self.node, self.codebase_name, self.dependencies)

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}


class FileTechDocTask(Task):
    def __init__(
        self,
        codebase_name: str,
        source_code: str,
        node: LiteNode,
        task_name: str,
        source_content_id: uuid.UUID,
    ):
        self.codebase_name = codebase_name
        self.source_code = source_code
        self.node = node
        self.source_content_id = source_content_id
        super().__init__(task_name=task_name)

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> dict[str, any]:
        async with tech_docs_sem:
            success, docs, node = await make_tech_doc.remote.aio(
                node=self.node,
                source_code=self.source_code,
                codebase_name=self.codebase_name,
            )

        from sqlmodel.ext.asyncio.session import AsyncSession
        from database.db import async_engine

        async with database_sem:
            short_single_sentence_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.SHORT_SENTENCE_DESCRIPTION
            )
            short_single_paragraph_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.SHORT_PARAGRAPH_DESCRIPTION
            )
            long_descrip_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.LONG_DESCRIPTION
            )
            chunk_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.CHUNK_DESCRIPTIONS
            )

            # Short Single Sentence
            short_sent_dc = DerivedContent(
                content_type_id=short_single_sentence_dc_id,
                source_content_id=self.source_content_id,
                content=docs["short"]["single_sentence"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Short Single Paragraph
            short_para_dc = DerivedContent(
                content_type_id=short_single_paragraph_dc_id,
                source_content_id=self.source_content_id,
                content=docs["short"]["single_paragraph"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Long File Description
            long_desc_dc = DerivedContent(
                content_type_id=long_descrip_dc_id,
                source_content_id=self.source_content_id,
                content=docs["long"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Chunk Descriptions
            chunks_dc = []
            if len(docs["chunk_descriptions"]) > 1:
                for chunk in docs["chunk_descriptions"]:
                    chunk_dc = DerivedContent(
                        content_type_id=chunk_dc_id,
                        source_content_id=self.source_content_id,
                        content=chunk,
                        misc_metadata=None,
                        status=Enum_Derived_Content_Status.generation_complete,
                        order=0,
                    )
                    chunks_dc.append(chunk_dc)

            async with AsyncSession(async_engine) as session:
                # TODO: we aren't deleting here. When we create embeddings, we'll want to cascade
                # delete everything related to old derived content

                del_statement = delete(DerivedContent).where(
                    DerivedContent.source_content_id == self.source_content_id,
                    DerivedContent.content_type_id.in_(
                        [
                            chunk_dc_id,
                            short_single_paragraph_dc_id,
                            short_single_sentence_dc_id,
                            long_descrip_dc_id,
                        ]
                    ),
                )
                await session.exec(del_statement)
                await session.commit()

                dc_records = [short_sent_dc, short_para_dc, long_desc_dc]
                dc_records.extend(chunks_dc)
                session.add_all(dc_records)
                await session.commit()

        return {"success": success, "docs": docs}

    def hashable_attrs(self) -> tuple:
        return (self.task_name, self.node, self.codebase_name, self.source_code)

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}


class SymbolsTask(Task):
    def __init__(
        self,
        task_name: str,
        codebase_root: Path,
        node: LiteNode,
        source_code: str,
        tech_docs_task: FileTechDocTask,
        source_content_id: uuid.UUID,
    ):
        self.codebase_root = codebase_root
        self.node = node
        self.source_code = source_code
        self.tech_docs_task = tech_docs_task
        self.source_content_id = source_content_id
        super().__init__(task_name=task_name, dependencies=(tech_docs_task,))

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> dict[str, any]:
        tech_docs_result = dependent_results[self.tech_docs_task]
        file_summary = tech_docs_result.result["docs"]["short"]["single_paragraph"]
        symbol_count_limit = 500
        session_chunk_size = 25

        if tech_docs_result.result["success"] is False:
            symbols = []
        else:
            async with symbols_sem:
                symbols: list[dict[str, any]] = await make_symbol_docs.remote.aio(
                    node=self.node,
                    source_code=self.source_code,
                    file_description_paragraph=file_summary,
                    symbol_count_limit=symbol_count_limit,
                )

        from sqlmodel.ext.asyncio.session import AsyncSession
        from database.db import async_engine

        async with database_sem:
            symbol_derived_content_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.SYMBOL
            )
            symbol_dcs = []
            for idx, symbol in enumerate(symbols):
                symbol_dc = DerivedContent(
                    content_type_id=symbol_derived_content_id,
                    source_content_id=self.source_content_id,
                    content=None,
                    misc_metadata=symbol,
                    status=Enum_Derived_Content_Status.generation_complete,
                    order=idx,
                )
                symbol_dcs.append(symbol_dc)

            async with AsyncSession(async_engine) as session:
                del_statement = (
                    delete(DerivedContent)
                    .where(DerivedContent.source_content_id == self.source_content_id)
                    .where(DerivedContent.content_type_id == symbol_derived_content_id)
                )
                await session.exec(del_statement)
                await session.commit()

                for i in range(0, len(symbol_dcs), session_chunk_size):
                    session.add_all(symbol_dcs[i : i + session_chunk_size])
                    await session.commit()

        return {"symbols": symbols}

    def hashable_attrs(self) -> tuple:
        # Put class name in here too
        return (
            self.task_name,
            self.node,
            self.codebase_root,
            self.source_code,
            self.dependencies,
        )

    def recoverable_errors(self) -> set[type[Exception]]:
        return set()


class TopLevelDocsTask(Task):
    def __init__(
        self,
        codebase_name: str,
        ordered_tech_docs_tasks: tuple[TechDocsTask],
        source_content_id: uuid.UUID,
    ):
        self.codebase_name = codebase_name
        self.source_content_id = source_content_id
        super().__init__(
            task_name=f"TopLevelTechDocsTask of {codebase_name}",
            dependencies=ordered_tech_docs_tasks,
        )

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> dict[str, any]:
        # We put this data into the format expected by the top level task.
        # TODO: could this get too big to send over the container wire? The current limit of modal is 100MB
        children_nodes_to_docs = {
            task.node: dr.result["docs"]
            for task, dr in dependent_results.items()
            if dr.state == TaskResultKind.SUCCESS
        }
        docs = await make_toplevel_tech_docs.remote.aio(
            codebase_name=self.codebase_name,
            nodes_to_docs=children_nodes_to_docs,
        )

        async with database_sem:
            short_single_sentence_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.SHORT_SENTENCE_DESCRIPTION
            )
            short_single_paragraph_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.SHORT_PARAGRAPH_DESCRIPTION
            )
            terse_sentence_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.TERSE_SENTENCE_DESCRIPTION
            )
            long_descrip_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.LONG_DESCRIPTION
            )
            quickstart_use_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.QUICK_START_USE
            )
            quickstart_dependencies_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.QUICK_START_DEPENDENCIES
            )
            quickstart_entry_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.QUICK_START_ENTRY
            )
            quickstart_get_started_dc_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.QUICK_START_GETTING_STARTED
            )

            top_level_tups = [
                (short_single_sentence_dc_id, docs["short"]["single_sentence"]),
                (short_single_paragraph_dc_id, docs["short"]["single_paragraph"]),
                (terse_sentence_dc_id, docs["short"]["terse_sentence"]),
                (long_descrip_dc_id, docs["long"]),
                (quickstart_use_dc_id, docs["quickstart"]["use"]),
                (quickstart_dependencies_dc_id, docs["quickstart"]["dependencies"]),
                (quickstart_entry_dc_id, docs["quickstart"]["entry"]),
                (quickstart_get_started_dc_id, docs["quickstart"]["getting_started"]),
            ]

            dc_contents = []
            for dc_type_id, dc_docs in top_level_tups:
                dc = DerivedContent(
                    content_type_id=dc_type_id,
                    source_content_id=self.source_content_id,
                    content=dc_docs,
                    misc_metadata=None,
                    status=Enum_Derived_Content_Status.generation_complete,
                    order=0,
                )
                dc_contents.append(dc)

            from sqlmodel.ext.asyncio.session import AsyncSession
            from database.db import async_engine

            async with AsyncSession(async_engine) as session:
                # TODO: we aren't deleting here. When we create embeddings, we'll want to cascade
                # delete everything related to old derived content

                del_statement = delete(DerivedContent).where(
                    DerivedContent.source_content_id == self.source_content_id,
                    DerivedContent.content_type_id.in_(
                        [dc_id for dc_id, _ in top_level_tups]
                    ),
                )
                await session.exec(del_statement)
                await session.commit()

                session.add_all(dc_contents)
                await session.commit()

        return {"docs": docs}

    def hashable_attrs(self) -> tuple:
        return (self.task_name, self.codebase_name, self.dependencies)

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}
