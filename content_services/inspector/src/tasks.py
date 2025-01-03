import asyncio
import uuid
from typing import Union

from database.models_v1 import (
    ChunkAndEmbedding,
    DerivedContent,
)
from database.models_v2_enums import ContentKind
from modal_funcs import (
    make_folder_tech_doc,
    make_symbol_docs,
    make_tech_doc,
    make_toplevel_tech_docs,
)
from openai import OpenAIError
from sqlmodel import delete, select
from utils.dag import LiteNode
from utils.db import get_source_code_derived_content
from utils.task import Task, TaskResult, TaskResultKind

TechDocsTask = Union["FileTechDocTask", "FolderTechDocTask", "TopLevelDocsTask"]

# Semaphores below provide a simple way to cut down on rate limit errors with Open AI API
symbols_sem = asyncio.Semaphore(55)
tech_docs_sem = asyncio.Semaphore(40)
folder_tech_docs_sem = asyncio.Semaphore(20)
embed_sem = asyncio.Semaphore(10)

# Limits active DB connections for an individual inspector run
database_sem = asyncio.Semaphore(5)


class FolderTechDocTask(Task):
    def __init__(
        self,
        node: LiteNode,
        task_name: str,
        child_docs_tasks: tuple[TechDocsTask],
        codebase_name: str,
        db_node_id: uuid.UUID,  # TODO: this needs to be node_id
    ) -> None:
        self.child_docs_tasks = child_docs_tasks
        self.codebase_name = codebase_name
        self.db_node_id = db_node_id
        super().__init__(
            task_name=task_name,
            node=node,
            dependencies=child_docs_tasks,
        )

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
        return {"docs": docs}

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        docs = task_result.result["docs"]

        async with database_sem:
            # Short Single Sentence
            short_sent_dc = DerivedContent(
                content_type_id=None,
                content_kind=ContentKind.SHORT_SENTENCE_DESCRIPTION.value,  # "short_sentence_description",
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_sentence"],
                misc_metadata=None,
            )
            # Short Single Paragraph
            short_para_dc = DerivedContent(
                content_type_id=None,
                content_kind=ContentKind.SHORT_PARAGRAPH_DESCRIPTION.value,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_paragraph"],
                misc_metadata=None,
            )
            # Long File Description
            long_desc_dc = DerivedContent(
                content_type_id=None,
                content_kind=ContentKind.LONG_DESCRIPTION.value,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["long"],
                misc_metadata=None,
            )

            async with AsyncSession(async_engine) as session:
                dc_delete_query = delete(DerivedContent).where(
                    DerivedContent.node_id == self.db_node_id,
                    DerivedContent.content_kind.in_(
                        [
                            ContentKind.SHORT_SENTENCE_DESCRIPTION.value,
                            ContentKind.SHORT_PARAGRAPH_DESCRIPTION.value,
                            ContentKind.LONG_DESCRIPTION.value,
                        ]
                    ),
                )
                await session.exec(dc_delete_query)
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
        return {"content_ids": content_ids}

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}


class FileTechDocTask(Task):
    def __init__(
        self,
        codebase_name: str,
        source_code: str,
        node: LiteNode,
        task_name: str,
        db_node_id: uuid.UUID,
    ) -> None:
        self.codebase_name = codebase_name
        self.source_code = source_code
        self.db_node_id = db_node_id
        super().__init__(
            task_name=task_name,
            node=node,
        )

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> dict[str, any]:
        async with tech_docs_sem:
            success, docs, node = await make_tech_doc.remote.aio(
                node=self.node,
                source_code=self.source_code,
                codebase_name=self.codebase_name,
            )

        return {
            "success": success,
            "docs": docs,
        }

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        docs = task_result.result["docs"]
        async with database_sem:
            # Short Single Sentence
            short_sent_dc = DerivedContent(
                content_type_id=None,
                content_kind=ContentKind.SHORT_SENTENCE_DESCRIPTION.value,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_sentence"],
                misc_metadata=None,
            )
            # Short Single Paragraph
            short_para_dc = DerivedContent(
                content_type_id=None,
                content_kind=ContentKind.SHORT_PARAGRAPH_DESCRIPTION.value,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_paragraph"],
                misc_metadata=None,
            )
            # Long File Description
            long_desc_dc = DerivedContent(
                content_type_id=None,
                content_kind=ContentKind.LONG_DESCRIPTION.value,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["long"],
                misc_metadata=None,
            )
            # Chunk Descriptions
            chunks_dc = []
            if len(docs["chunk_descriptions"]) > 1:
                for i, chunk in enumerate(docs["chunk_descriptions"]):
                    chunk_dc = DerivedContent(
                        content_type_id=None,
                        content_kind=ContentKind.CHUNK_DESCRIPTIONS.value,
                        node_id=self.db_node_id,
                        relative_path=str(self.node.root_rel_path),
                        content=chunk,
                        misc_metadata=None,
                        order=i,
                    )
                    chunks_dc.append(chunk_dc)

            async with AsyncSession(async_engine) as session:
                dc_delete_query = delete(DerivedContent).where(
                    DerivedContent.node_id == self.db_node_id,
                    DerivedContent.content_kind.in_(
                        [
                            ContentKind.CHUNK_DESCRIPTIONS.value,
                            ContentKind.SHORT_SENTENCE_DESCRIPTION.value,
                            ContentKind.SHORT_PARAGRAPH_DESCRIPTION.value,
                            ContentKind.LONG_DESCRIPTION.value,
                        ]
                    ),
                )
                await session.exec(dc_delete_query)
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
        return {"content_ids": content_ids}

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}


class SymbolsTask(Task):
    def __init__(
        self,
        task_name: str,
        node: LiteNode,
        source_code: str,
        tech_docs_task: FileTechDocTask,
        db_node_id: uuid.UUID,
    ) -> None:
        self.source_code = source_code
        self.tech_docs_task = tech_docs_task
        self.db_node_id = db_node_id
        super().__init__(
            task_name=task_name,
            node=node,
            dependencies=(tech_docs_task,),
        )

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> dict[str, any]:
        tech_docs_result = dependent_results[self.tech_docs_task]
        file_summary = tech_docs_result.result["docs"]["short"]["single_paragraph"]
        symbol_count_limit = 500

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

        return {"symbols": symbols}

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        session_chunk_size = 25
        symbols = task_result.result["symbols"]

        async with database_sem:
            symbol_dcs = []
            for idx, symbol in enumerate(symbols):
                symbol_dc = DerivedContent(
                    content_type_id=None,
                    content_kind=ContentKind.SYMBOL.value,
                    node_id=self.db_node_id,
                    relative_path=str(self.node.root_rel_path),
                    content=None,
                    misc_metadata=symbol,
                    order=idx,
                )
                symbol_dcs.append(symbol_dc)

            async with AsyncSession(async_engine) as session:
                dc_delete_query = (
                    delete(DerivedContent)
                    .where(DerivedContent.node_id == self.db_node_id)
                    .where(DerivedContent.content_kind == ContentKind.SYMBOL.value)
                )
                await session.exec(dc_delete_query)
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
        return {"content_ids": content_ids}

    def recoverable_errors(self) -> set[type[Exception]]:
        return set()


class TopLevelDocsTask(Task):
    def __init__(
        self,
        node: LiteNode,
        codebase_name: str,
        ordered_tech_docs_tasks: tuple[TechDocsTask],
        db_node_id: uuid.UUID,
    ) -> None:
        self.codebase_name = codebase_name
        self.db_node_id = db_node_id
        super().__init__(
            task_name=f"TopLevelTechDocsTask of {codebase_name}",
            node=node,
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

        return {"docs": docs}

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        docs = task_result.result["docs"]

        async with database_sem:
            # TODO: add types for top level sentence/paragraph/etc.
            # TODO: content_type is now just a string, inserted as content_type_kind on DerivedContent
            # short_single_sentence_dc_id = await get_derived_content_type_uuid(
            #     DerivedContentTypeMap.SHORT_SENTENCE_DESCRIPTION
            # )
            # short_single_paragraph_dc_id = await get_derived_content_type_uuid(
            #     DerivedContentTypeMap.SHORT_PARAGRAPH_DESCRIPTION
            # )
            # terse_sentence_dc_id = await get_derived_content_type_uuid(
            #     DerivedContentTypeMap.TERSE_SENTENCE_DESCRIPTION
            # )
            # long_descrip_dc_id = await get_derived_content_type_uuid(
            #     DerivedContentTypeMap.LONG_DESCRIPTION
            # )

            top_level_tups = [
                (
                    ContentKind.TOP_LEVEL_SHORT_SENTENCE.value,
                    docs["short"]["single_sentence"],
                ),
                (
                    ContentKind.TOP_LEVEL_SHORT_PARAGRAPH.value,
                    docs["short"]["single_paragraph"],
                ),
                (
                    ContentKind.TOP_LEVEL_TERSE_SENTENCE.value,
                    docs["short"]["terse_sentence"],
                ),
                (ContentKind.TOP_LEVEL_LONG_DESCRIPTION.value, docs["long"]),
            ]

            dc_contents = []
            for content_kind, dc_docs in top_level_tups:
                dc = DerivedContent(
                    content_type_id=None,
                    content_kind=content_kind,
                    node_id=self.db_node_id,
                    relative_path=str(self.node.root_rel_path),
                    content=dc_docs,
                    misc_metadata=None,
                )
                dc_contents.append(dc)

            from database.db import async_engine
            from sqlmodel.ext.asyncio.session import AsyncSession

            async with AsyncSession(async_engine) as session:
                dc_delete_query = delete(DerivedContent).where(
                    DerivedContent.node_id == self.db_node_id,
                    DerivedContent.content_kind.in_(
                        [dc_slug for dc_slug, _ in top_level_tups]
                    ),
                )
                await session.exec(dc_delete_query)
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
        return {"content_ids": content_ids}

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}


class EmbeddingTask(Task):
    def __init__(
        self,
        node: LiteNode,
        task_name: str,
        source_code: str | None = None,
        db_node_id: uuid.UUID | None = None,
        dependent_tasks: list[Task] | None = None,
    ) -> None:
        if source_code and not all([source_code, db_node_id]):
            raise ValueError(
                "If source_code is provided, source_content_id must also be provided"
            )

        self.source_code = source_code
        self.db_node_id = db_node_id

        dependent_tasks = dependent_tasks or []
        deduped_tasks = tuple(set(dependent_tasks))
        super().__init__(
            task_name=task_name,
            node=node,
            dependencies=deduped_tasks,
        )

    # TODO: for PoC we moved the chunking/embedding AND IO into post-run-io, but this is not ideal. But it was the quickest way to get it working.
    # We should move the chunking/embedding into run_implementation and the IO into post-run-io

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> dict[str, any]:
        return {}

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        from database.db import async_engine
        from database.models_v1 import ChunkAndEmbedding
        from sqlmodel.ext.asyncio.session import AsyncSession

        if self.db_node_id:
            source_code_derived_content = await get_source_code_derived_content(
                self.db_node_id
            )
            source_code_dc_id = source_code_derived_content.id
        else:
            source_code_dc_id = None

        content_kinds_to_embed = [
            ContentKind.LONG_DESCRIPTION.value,
            ContentKind.SYMBOL.value,
        ]
        # TODO: type names are just strings now

        for task, dr in dependent_io_results.items():
            content_ids_to_embed = [
                uuid.UUID(uid) for uid in dr["content_ids"]
            ]  # TODO may not be needed

            async with database_sem, AsyncSession(async_engine) as session:
                # TODO: modify for (content_type) kind
                contents_query = select(DerivedContent).where(
                    DerivedContent.id.in_(content_ids_to_embed),
                    DerivedContent.content_kind.in_(content_kinds_to_embed),
                )
                print(f"Querying '{task.task_name}' content to embed")
                result = await session.exec(contents_query)
                content_rows = result.all()
                print(f"Queried {len(content_rows)} for '{task.task_name}'")
                if not content_rows:
                    continue
                body = [
                    (c.content, c.id, c.content_kind, c.misc_metadata)
                    for c in content_rows
                ]
                contents, ids, type_names, metadata = zip(*body, strict=False)
            print(f"Chunking {len(contents)} contents for {task.task_name}")

            # Chunk, embed, and write the chunks based on source content ids
            # TODO: modify type_names for kinds
            chunks = await self.chunk_embed_and_prep_for_db(
                list(contents), list(ids), list(type_names), list(metadata)
            )
            print(f"Embedded {len(chunks)} chunks for '{task.task_name}'")

            async with database_sem, AsyncSession(async_engine) as session:  # noqa: SIM117
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
            # TODO: this is node_id
            # TODO: chunkandembedding needs to point at a piece of content, but we don't store the source code on the database
            sc_chunks = await self.chunk_embed_and_prep_for_db(
                [self.source_code],
                [source_code_dc_id],
                [ContentKind.CODEBASE_FILE.value],
                [{}],
            )

            async with database_sem, AsyncSession(async_engine) as session:  # noqa: SIM117
                async with session.begin():
                    delete_statement = delete(ChunkAndEmbedding).where(
                        ChunkAndEmbedding.content_id == source_code_dc_id
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
        content_types: list[str],  # TODO: content_types will be kind
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
            async with embed_sem:
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

    def recoverable_errors(self) -> set[type[Exception]]:
        return {OpenAIError}
