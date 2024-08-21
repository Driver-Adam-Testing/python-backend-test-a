import asyncio
import uuid
from typing import Union

from database.models_v1 import (
    ChunkAndEmbedding,
    DerivedContent,
    Enum_Derived_Content_Status,
)
from modal_funcs import (
    make_folder_tech_doc,
    make_symbol_docs,
    make_tech_doc,
    make_toplevel_tech_docs,
)
from openai import OpenAIError
from sqlalchemy.orm import selectinload
from sqlmodel import delete, select
from utils.dag import LiteNode
from utils.db import (
    DerivedContentTypeMap,
    get_derived_content_type_uuid,
    get_rel_path_workspace_id_codebase_id_from_source_content_id,
)
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

        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

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
            (
                _,
                workspace_id,
                codebase_id,
            ) = await get_rel_path_workspace_id_codebase_id_from_source_content_id(
                self.source_content_id
            )

            # Short Single Sentence
            short_sent_dc = DerivedContent(
                content_type_id=short_single_sentence_dc_id,
                source_content_id=self.source_content_id,
                workspace_id=workspace_id,
                codebase_id=codebase_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_sentence"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Short Single Paragraph
            short_para_dc = DerivedContent(
                content_type_id=short_single_paragraph_dc_id,
                source_content_id=self.source_content_id,
                workspace_id=workspace_id,
                codebase_id=codebase_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_paragraph"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Long File Description
            long_desc_dc = DerivedContent(
                content_type_id=long_descrip_dc_id,
                source_content_id=self.source_content_id,
                workspace_id=workspace_id,
                codebase_id=codebase_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["long"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )

            async with AsyncSession(async_engine) as session:
                # TODO: we aren't deleting here. When we create embeddings, we'll want to cascade
                # delete everything related to old derived content

                dc_query = select(DerivedContent).where(
                    DerivedContent.source_content_id == self.source_content_id,
                    DerivedContent.content_type_id.in_(
                        [
                            short_single_paragraph_dc_id,
                            short_single_sentence_dc_id,
                            long_descrip_dc_id,
                        ]
                    ),
                )
                result = await session.exec(dc_query)
                dc_rows = result.all()
                for dc_row in dc_rows:
                    await session.delete(dc_row)
                await session.commit()

                dc_records = [short_sent_dc, short_para_dc, long_desc_dc]
                session.add_all(dc_records)
                await session.commit()

                content_ids = []
                for record in dc_records:
                    await session.refresh(record)
                    content_ids.append(record.id)
                content_ids = [
                    str(cid) for cid in content_ids
                ]  # Must be json serializable... TODO
        return {"docs": docs, "content_ids": content_ids}

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

        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

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

            (
                _,
                workspace_id,
                codebase_id,
            ) = await get_rel_path_workspace_id_codebase_id_from_source_content_id(
                self.source_content_id
            )

            # Short Single Sentence
            short_sent_dc = DerivedContent(
                content_type_id=short_single_sentence_dc_id,
                source_content_id=self.source_content_id,
                workspace_id=workspace_id,
                codebase_id=codebase_id,
                relative_path=str(node.root_rel_path),
                content=docs["short"]["single_sentence"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Short Single Paragraph
            short_para_dc = DerivedContent(
                content_type_id=short_single_paragraph_dc_id,
                source_content_id=self.source_content_id,
                workspace_id=workspace_id,
                codebase_id=codebase_id,
                relative_path=str(node.root_rel_path),
                content=docs["short"]["single_paragraph"],
                misc_metadata=None,
                status=Enum_Derived_Content_Status.generation_complete,
                order=0,
            )
            # Long File Description
            long_desc_dc = DerivedContent(
                content_type_id=long_descrip_dc_id,
                source_content_id=self.source_content_id,
                workspace_id=workspace_id,
                codebase_id=codebase_id,
                relative_path=str(node.root_rel_path),
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
                        workspace_id=workspace_id,
                        codebase_id=codebase_id,
                        relative_path=str(node.root_rel_path),
                        content=chunk,
                        misc_metadata=None,
                        status=Enum_Derived_Content_Status.generation_complete,
                        order=0,
                    )
                    chunks_dc.append(chunk_dc)

            async with AsyncSession(async_engine) as session:
                # TODO: we aren't deleting here. When we create embeddings, we'll want to cascade
                # delete everything related to old derived content

                dc_query = select(DerivedContent).where(
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
                result = await session.exec(dc_query)
                dc_rows = result.all()
                for dc_row in dc_rows:
                    await session.delete(dc_row)
                await session.commit()

                dc_records = [short_sent_dc, short_para_dc, long_desc_dc]
                dc_records.extend(chunks_dc)
                session.add_all(dc_records)
                await session.commit()

                content_ids = []
                for record in dc_records:
                    await session.refresh(record)
                    content_ids.append(record.id)
                content_ids = [
                    str(cid) for cid in content_ids
                ]  # Make json serializable for result writer by converting to string... TODO

        return {
            "success": success,
            "docs": docs,
            "content_ids": content_ids,
        }

    def hashable_attrs(self) -> tuple:
        return (self.task_name, self.node, self.codebase_name, self.source_code)

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}


class SymbolsTask(Task):
    def __init__(
        self,
        task_name: str,
        node: LiteNode,
        source_code: str,
        tech_docs_task: FileTechDocTask,
        source_content_id: uuid.UUID,
    ):
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

        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with database_sem:
            symbol_derived_content_id = await get_derived_content_type_uuid(
                DerivedContentTypeMap.SYMBOL
            )

            (
                _,
                workspace_id,
                codebase_id,
            ) = await get_rel_path_workspace_id_codebase_id_from_source_content_id(
                self.source_content_id
            )

            symbol_dcs = []
            for idx, symbol in enumerate(symbols):
                symbol_dc = DerivedContent(
                    content_type_id=symbol_derived_content_id,
                    source_content_id=self.source_content_id,
                    workspace_id=workspace_id,
                    codebase_id=codebase_id,
                    relative_path=str(self.node.root_rel_path),
                    content=None,
                    misc_metadata=symbol,
                    status=Enum_Derived_Content_Status.generation_complete,
                    order=idx,
                )
                symbol_dcs.append(symbol_dc)

            async with AsyncSession(async_engine) as session:
                dc_query = (
                    select(DerivedContent)
                    .where(DerivedContent.source_content_id == self.source_content_id)
                    .where(DerivedContent.content_type_id == symbol_derived_content_id)
                )
                result = await session.exec(dc_query)
                dc_rows = result.all()
                for dc_row in dc_rows:
                    await session.delete(dc_row)
                await session.commit()

                for i in range(0, len(symbol_dcs), session_chunk_size):
                    session.add_all(symbol_dcs[i : i + session_chunk_size])
                    await session.commit()

                content_ids = []
                for record in symbol_dcs:
                    await session.refresh(record)
                    content_ids.append(record.id)
                content_ids = [
                    str(cid) for cid in content_ids
                ]  # Must be json serializable... TODO

        return {"symbols": symbols, "content_ids": content_ids}

    def hashable_attrs(self) -> tuple:
        # Put class name in here too
        return (
            self.task_name,
            self.node,
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

            (
                relative_path,
                workspace_id,
                codebase_id,
            ) = await get_rel_path_workspace_id_codebase_id_from_source_content_id(
                self.source_content_id
            )

            dc_contents = []
            for dc_type_id, dc_docs in top_level_tups:
                dc = DerivedContent(
                    content_type_id=dc_type_id,
                    source_content_id=self.source_content_id,
                    workspace_id=workspace_id,
                    codebase_id=codebase_id,
                    relative_path=relative_path,
                    content=dc_docs,
                    misc_metadata=None,
                    status=Enum_Derived_Content_Status.generation_complete,
                    order=0,
                )
                dc_contents.append(dc)

            from database.db import async_engine
            from sqlmodel.ext.asyncio.session import AsyncSession

            async with AsyncSession(async_engine) as session:
                # TODO: we aren't deleting here. When we create embeddings, we'll want to cascade
                # delete everything related to old derived content
                dc_query = select(DerivedContent).where(
                    DerivedContent.source_content_id == self.source_content_id,
                    DerivedContent.content_type_id.in_(
                        [dc_id for dc_id, _ in top_level_tups]
                    ),
                )
                result = await session.exec(dc_query)
                dc_rows = result.all()
                for dc_row in dc_rows:
                    await session.delete(dc_row)
                await session.commit()

                session.add_all(dc_contents)
                await session.commit()

                content_ids = []
                for record in dc_contents:
                    await session.refresh(record)
                    content_ids.append(record.id)
                content_ids = [
                    str(cid) for cid in content_ids
                ]  # Must be json serializable... TODO

        return {"docs": docs, "content_ids": content_ids}

    def hashable_attrs(self) -> tuple:
        return (self.task_name, self.codebase_name, self.dependencies)

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}


class EmbeddingTask(Task):
    def __init__(
        self,
        task_name: str,
        source_code: str | None = None,
        source_content_id: uuid.UUID | None = None,
        dependent_tasks: list[Task] | None = None,
    ):
        if source_code:
            if not all([source_code, source_content_id]):
                raise ValueError(
                    "If source_code is provided, source_content_id must also be provided"
                )

        self.source_code = source_code
        self.source_code_sc_id = source_content_id

        dependent_tasks = dependent_tasks or []
        deduped_tasks = tuple(set(dependent_tasks))
        super().__init__(task_name=task_name, dependencies=deduped_tasks)

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> dict[str, any]:
        # TODO can we move imports here up?
        from database.db import async_engine
        from database.models_v1 import ChunkAndEmbedding, DerivedContentType
        from sqlmodel.ext.asyncio.session import AsyncSession

        type_names_to_embed = [
            "long_description",
            "symbol",
        ]

        for task, dr in dependent_results.items():
            content_ids_to_embed = [
                uuid.UUID(uid) for uid in dr.result["content_ids"]
            ]  # TODO may not be needed

            async with database_sem:
                async with AsyncSession(async_engine) as session:
                    contents_query = (
                        select(DerivedContent)
                        .join(
                            DerivedContentType,
                            DerivedContent.content_type_id == DerivedContentType.id,
                        )
                        .where(
                            DerivedContent.id.in_(content_ids_to_embed),
                            DerivedContentType.type_name.in_(type_names_to_embed),
                        )
                        .options(selectinload(DerivedContent.content_type))
                    )
                    print(f"Querying '{task.task_name}' content to embed")
                    result = await session.exec(contents_query)
                    content_rows = result.all()
                    print(f"Queried {len(content_rows)} for '{task.task_name}'")
                    if not content_rows:
                        continue
                    body = [
                        (c.content, c.id, c.content_type.type_name, c.misc_metadata)
                        for c in content_rows
                    ]
                    contents, ids, type_names, metadata = zip(*body, strict=False)
            print(f"Chunking {len(contents)} contents for {task.task_name}")

            # Chunk, embed, and write the chunks based on source content ids
            chunks = await self.chunk_embed_and_prep_for_db(
                list(contents), list(ids), list(type_names), list(metadata)
            )
            print(f"Embedded {len(chunks)} chunks for '{task.task_name}'")

            async with database_sem:
                async with AsyncSession(async_engine) as session:
                    async with session.begin():
                        for cid in ids:
                            delete_statement = delete(ChunkAndEmbedding).where(
                                ChunkAndEmbedding.content_id == cid
                            )
                            await session.exec(delete_statement)
                        session.add_all(chunks)
                        await session.commit()
            print(f"Saved {len(chunks)} for {task.task_name} to database")

        # Chunk, embed, and write source code if provided
        # TODO it's super hacky to embed source code directly like this.
        # Since we will move importing of source code into inspector, we will not need this special pattern
        # in the future. We will have separate tasks for loading source code and creating the source content.
        if self.source_code:
            # Chunk, embed, and write source code
            sc_chunks = await self.chunk_embed_and_prep_for_db(
                [self.source_code],
                [self.source_code_sc_id],
                ["source-file"],
                [{}],
            )

            async with database_sem:
                async with AsyncSession(async_engine) as session:
                    async with session.begin():
                        delete_statement = delete(ChunkAndEmbedding).where(
                            ChunkAndEmbedding.content_id == self.source_code_sc_id
                        )
                        await session.exec(delete_statement)
                        session.add_all(sc_chunks)
                        await session.commit()
            print(
                f"Saved {len(sc_chunks)} chunks of source code for task '{self.task_name}' to database"
            )

        return {}

    @staticmethod
    async def chunk_embed_and_prep_for_db(
        contents: list[str],
        content_ids: list[uuid.UUID],
        content_types: list[str],
        metadatas: list[dict[str, any]],
    ) -> list[ChunkAndEmbedding]:
        from database.models_v1 import ChunkAndEmbedding
        from shared.chunking.text_splitter import split_text
        from shared.embedding.text_embedder import async_batch_embed_text

        chunks = []
        for content, content_id, content_type, metadata in zip(
            contents, content_ids, content_types, metadatas, strict=False
        ):
            if content_type == "symbol":
                content = metadata.get("description")
                if not content:
                    continue

            split_documents = split_text(content)
            embeds = await async_batch_embed_text([d.text for d in split_documents])
            chunks.extend(
                [
                    ChunkAndEmbedding(
                        text_embedding_3_small=e,
                        text=d.text,
                        content_id=content_id,
                        chunk_number=i,
                        token_count=len(d.tokens),
                    )
                    for i, (d, e) in enumerate(
                        zip(split_documents, embeds, strict=False)
                    )
                ]
            )
        return chunks

    def hashable_attrs(self) -> tuple:
        return (self.task_name, self.dependencies)

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}
