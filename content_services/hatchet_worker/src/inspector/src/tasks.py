import asyncio
import concurrent.futures
import uuid
from pathlib import Path
from typing import Optional, Union

from database.models import (
    ChunkAndEmbedding,
    DerivedContent,
)
from database.models_enums import ContentKind
from shared.inspector.utils.dag import LiteNode
from shared.inspector.utils.db import get_source_code_derived_content
from shared.inspector.utils.symbol_table import build_symbol_table
from shared.inspector.utils.task import (
    SerializationMethod,
    Task,
    TaskResult,
    TaskWorkUnits,
)
from sqlmodel import delete, select
from workflows.inspector_functions import (
    CodebaseTagsInput,
    FolderDocInput,
    SymbolDocInput,
    TechDocInput,
    TopLevelDocInput,
    codebase_tags_task,
    folder_doc_task,
    symbol_doc_task,
    tech_doc_task,
    toplevel_doc_task,
)

TechDocsTask = Union["FileTechDocTask", "FolderTechDocTask", "TopLevelDocsTask"]

# Semaphores below provide a simple way to cut down on rate limit errors with Open AI API
# The symbols and tech docs semaphores are set to 154 to be 4 above the concurrency limit on the modal functions.
# Somewhat arbitrary; we just want a few more than modal concurrency for expediency in kicking off the next task
# when one completes
symbols_sem = asyncio.Semaphore(76)
tech_docs_sem = asyncio.Semaphore(76)
folder_tech_docs_sem = asyncio.Semaphore(64)

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
        previous_content: dict[str, str] | None = None,
    ) -> None:
        self.child_docs_tasks = child_docs_tasks
        self.codebase_name = codebase_name
        self.db_node_id = db_node_id
        self.previous_content = previous_content
        super().__init__(
            task_name=task_name,
            node=node,
            dependencies=child_docs_tasks,
        )

    async def run_implementation(
        self, dependent_results: dict[TechDocsTask, TaskResult]
    ) -> TaskResult:
        # Here, we know we have results for all the child nodes, so processing can commence.
        # We only want to use the results that were successful to prevent folder docs failures due to files that failed to process
        child_nodes_to_docs = {
            task.node: dr.data["docs"] for task, dr in dependent_results.items()
        }
        async with folder_tech_docs_sem:
            child_nodes_to_docs_list = list(child_nodes_to_docs.items())
            folder_doc_input = FolderDocInput(
                node=self.node,
                codebase_name=self.codebase_name,
                child_nodes_to_docs=child_nodes_to_docs_list,
                previous_content=self.previous_content,
            )
            docs = await folder_doc_task.aio_run(folder_doc_input)
        return TaskResult(data={"docs": docs}, serialization=SerializationMethod.JSON)

    @property
    def work_units(self) -> int:
        return TaskWorkUnits.FOLDER_TECH_DOC

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        docs = task_result.data["docs"]

        async with database_sem:
            # Short Single Sentence
            short_sent_dc = DerivedContent(
                content_kind=ContentKind.SHORT_SENTENCE_DESCRIPTION,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_sentence"],
                misc_metadata=None,
            )
            # Short Single Paragraph
            short_para_dc = DerivedContent(
                content_kind=ContentKind.SHORT_PARAGRAPH_DESCRIPTION,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_paragraph"],
                misc_metadata=None,
            )
            # Long File Description
            long_desc_dc = DerivedContent(
                content_kind=ContentKind.LONG_DESCRIPTION,
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
                            ContentKind.SHORT_SENTENCE_DESCRIPTION,
                            ContentKind.SHORT_PARAGRAPH_DESCRIPTION,
                            ContentKind.LONG_DESCRIPTION,
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
                content_ids = [str(cid) for cid in content_ids]
        return {"content_ids": content_ids}


class FileTechDocTask(Task):
    def __init__(
        self,
        codebase_name: str,
        source_code: str,
        node: LiteNode,
        task_name: str,
        db_node_id: uuid.UUID,
        version_id: str,
        symbol_table_task: Optional["CSymbolTableTask"],
        thread_pool: concurrent.futures.ThreadPoolExecutor | None = None,
    ) -> None:
        self.codebase_name = codebase_name
        self.source_code = source_code
        self.db_node_id = db_node_id
        self.version_id = version_id
        self.symbol_table_task = symbol_table_task
        self.thread_pool = thread_pool
        super().__init__(
            task_name=task_name,
            node=node,
            dependencies=[symbol_table_task] if symbol_table_task else [],
        )

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> TaskResult:
        async with tech_docs_sem:
            tech_doc_input = TechDocInput(
                node=self.node,
                codebase_name=self.codebase_name,
                source_code=self.source_code,
                version_id=self.version_id,
            )
            task_result = await tech_doc_task.aio_run(
                tech_doc_input,
            )
            success = task_result["success"]
            docs = task_result["file_doc"]

        return TaskResult(
            data={
                "success": success,
                "docs": docs,
            },
            serialization=SerializationMethod.JSON,
        )

    @property
    def work_units(self) -> int:
        return TaskWorkUnits.FILE_TECH_DOC

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        docs = task_result.data["docs"]
        async with database_sem:
            # Short Single Sentence
            short_sent_dc = DerivedContent(
                content_kind=ContentKind.SHORT_SENTENCE_DESCRIPTION,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_sentence"],
                misc_metadata=None,
            )
            # Short Single Paragraph
            short_para_dc = DerivedContent(
                content_kind=ContentKind.SHORT_PARAGRAPH_DESCRIPTION,
                node_id=self.db_node_id,
                relative_path=str(self.node.root_rel_path),
                content=docs["short"]["single_paragraph"],
                misc_metadata=None,
            )
            # Long File Description
            long_desc_dc = DerivedContent(
                content_kind=ContentKind.LONG_DESCRIPTION,
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
                        content_kind=ContentKind.CHUNK_DESCRIPTIONS,
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
                            ContentKind.CHUNK_DESCRIPTIONS,
                            ContentKind.SHORT_SENTENCE_DESCRIPTION,
                            ContentKind.SHORT_PARAGRAPH_DESCRIPTION,
                            ContentKind.LONG_DESCRIPTION,
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
                content_ids = [str(cid) for cid in content_ids]
        return {"content_ids": content_ids}


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
    ) -> TaskResult:
        tech_docs_result = dependent_results[self.tech_docs_task]
        file_summary = tech_docs_result.data["docs"]["short"]["single_paragraph"]
        symbol_count_limit = 500

        if tech_docs_result.data["success"] is False:
            symbols = []
        else:
            async with symbols_sem:
                symbol_doc_input = SymbolDocInput(
                    node=self.node,
                    source_code=self.source_code,
                    file_description_paragraph=file_summary,
                    symbol_count_limit=symbol_count_limit,
                )
                symbols: list[dict[str, any]] = await symbol_doc_task.aio_run(
                    symbol_doc_input
                )

        return TaskResult(
            data={"symbols": symbols}, serialization=SerializationMethod.JSON
        )

    @property
    def work_units(self) -> int:
        return TaskWorkUnits.SYMBOLS

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        from database.db import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        session_chunk_size = 25
        symbols = task_result.data["symbols"]

        async with database_sem:
            symbol_dcs = []
            for idx, symbol in enumerate(symbols):
                symbol_dc = DerivedContent(
                    content_kind=ContentKind.SYMBOL,
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
                    .where(DerivedContent.content_kind == ContentKind.SYMBOL)
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
                content_ids = [str(cid) for cid in content_ids]
        return {"content_ids": content_ids}


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
    ) -> TaskResult:
        # We put this data into the format expected by the top level task.
        # TODO: could this get too big to send over the container wire? The current limit of modal is 100MB
        children_nodes_to_docs = {
            task.node: dr.data["docs"] for task, dr in dependent_results.items()
        }
        toplevel_doc_input = TopLevelDocInput(
            codebase_name=self.codebase_name,
            nodes_to_docs=list(children_nodes_to_docs.items()),
        )
        docs = await toplevel_doc_task.aio_run(toplevel_doc_input)

        return TaskResult(data={"docs": docs}, serialization=SerializationMethod.JSON)

    @property
    def work_units(self) -> int:
        return TaskWorkUnits.TOP_LEVEL_DOCS

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        docs = task_result.data["docs"]

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
                    ContentKind.TOP_LEVEL_SHORT_SENTENCE,
                    docs["short"]["single_sentence"],
                ),
                (
                    ContentKind.TOP_LEVEL_SHORT_PARAGRAPH,
                    docs["short"]["single_paragraph"],
                ),
                (
                    ContentKind.TOP_LEVEL_TERSE_SENTENCE,
                    docs["short"]["terse_sentence"],
                ),
                (ContentKind.TOP_LEVEL_LONG_DESCRIPTION, docs["long"]),
            ]

            dc_contents = []
            for content_kind, dc_docs in top_level_tups:
                dc = DerivedContent(
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
                content_ids = [str(cid) for cid in content_ids]
        return {"content_ids": content_ids}


class CodebaseTaggingTask(Task):
    def __init__(
        self,
        root_node: LiteNode,
        codebase_name: str,
        ordered_tech_docs_tasks: tuple[TechDocsTask],
        db_root_node_id: uuid.UUID,
        previous_root_node_metadata: dict[ContentKind, list[dict]] | None = None,
    ) -> None:
        # NOTE: since the root node is always marked as modified on a diff update, we know this code will
        # execute every time a codebase is updated.
        self.codebase_name = codebase_name
        self.db_root_node_id = db_root_node_id
        self.previous_root_node_metadata = previous_root_node_metadata
        super().__init__(
            task_name=f"CodebaseTaggingTask of {codebase_name}",
            node=root_node,
            dependencies=ordered_tech_docs_tasks,
        )

    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> TaskResult:
        # We put this data into the format expected by the top level task.
        # TODO: could this get too big to send over the container wire? The current limit of modal is 100MB
        required_content_kinds = {
            ContentKind.CODEBASE_AUDIENCES,
            ContentKind.CODEBASE_DOMAINS,
            ContentKind.CODEBASE_KINDS,
            ContentKind.CODEBASE_ENTRY_POINTS,
        }
        if self.previous_root_node_metadata is not None:
            content_kinds_to_compute = {
                content_kind
                for content_kind in required_content_kinds
                if content_kind not in self.previous_root_node_metadata
            }
            existing_tags = {
                content_kind: self.previous_root_node_metadata[content_kind]
                for content_kind in required_content_kinds
                if content_kind in self.previous_root_node_metadata
            }
        else:
            # If no previous content, we need to compute all the tags
            content_kinds_to_compute = required_content_kinds
            existing_tags = {}

        if len(content_kinds_to_compute) == 0:
            # collect existing content and return
            return TaskResult(
                data=existing_tags, serialization=SerializationMethod.JSON
            )
        else:
            children_nodes_to_docs = {
                task.node: dr.data["docs"] for task, dr in dependent_results.items()
            }
            tags = await codebase_tags_task.aio_run(
                CodebaseTagsInput(
                    codebase_name=self.codebase_name,
                    nodes_to_docs=list(children_nodes_to_docs.items()),
                    content_kinds=content_kinds_to_compute,
                )
            )

        return TaskResult(
            data={**tags, **existing_tags}, serialization=SerializationMethod.JSON
        )

    @property
    def work_units(self) -> int:
        return TaskWorkUnits.TAGS

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        tags = task_result.data

        async with database_sem:
            tag_tups = [
                (
                    ContentKind.CODEBASE_AUDIENCES,
                    tags[ContentKind.CODEBASE_AUDIENCES],
                ),
                (
                    ContentKind.CODEBASE_DOMAINS,
                    tags[ContentKind.CODEBASE_DOMAINS],
                ),
                (ContentKind.CODEBASE_KINDS, tags[ContentKind.CODEBASE_KINDS]),
                (
                    ContentKind.CODEBASE_ENTRY_POINTS,
                    tags[ContentKind.CODEBASE_ENTRY_POINTS],
                ),
            ]

            dc_contents = []
            for content_kind, dc_tags in tag_tups:
                for tag in dc_tags:
                    dc = DerivedContent(
                        content_kind=content_kind,
                        node_id=self.db_root_node_id,
                        relative_path=str(self.node.root_rel_path),
                        content=None,
                        misc_metadata=tag,
                    )
                    dc_contents.append(dc)

            from database.db import async_engine
            from sqlmodel.ext.asyncio.session import AsyncSession

            async with AsyncSession(async_engine) as session:
                dc_delete_query = delete(DerivedContent).where(
                    DerivedContent.node_id == self.db_root_node_id,
                    DerivedContent.content_kind.in_(
                        [dc_slug for dc_slug, _ in tag_tups]
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
                content_ids = [str(cid) for cid in content_ids]
        return {"content_ids": content_ids}


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
            raise ValueError("If source_code is provided must also be provided")

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
        return TaskResult(data={}, serialization=SerializationMethod.JSON)

    @property
    def work_units(self) -> int:
        return TaskWorkUnits.EMBEDDING

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        from database.db import async_engine
        from database.models import ChunkAndEmbedding
        from sqlmodel.ext.asyncio.session import AsyncSession

        if self.db_node_id:
            async with database_sem:
                source_code_derived_content = await get_source_code_derived_content(
                    self.db_node_id
                )
                source_code_dc_id = source_code_derived_content.id
        else:
            source_code_dc_id = None

        content_kinds_to_embed = [
            ContentKind.LONG_DESCRIPTION,
            ContentKind.SYMBOL,
        ]
        # TODO: type names are just strings now

        for task, dr in dependent_io_results.items():
            if isinstance(task, CSymbolTableTask):
                continue
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
                [ContentKind.CODEBASE_FILE],
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
        from database.models import ChunkAndEmbedding
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


class CSymbolTableTask(Task):
    def __init__(
        self,
        root_node: LiteNode,
        task_name: str,
        codebase_name: str,
        codebase_root: Path,
        nodes_relative_paths: list[Path],
        version_id: str,
    ) -> None:
        self.codebase_name = codebase_name
        self.codebase_root = codebase_root
        self.files = {codebase_root / rel_path for rel_path in nodes_relative_paths}
        self.version_id = version_id
        self.storage_path = f"{version_id}_symbol_table.pkl"
        super().__init__(
            task_name=task_name,
            node=root_node,
        )

    async def run_implementation(
        self, dependent_results: dict[Task, TaskResult]
    ) -> TaskResult:
        print("Running CSymbolTableTask")
        # Pass all files to the unified builder - it will group by language automatically
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            file_to_symbols = await loop.run_in_executor(
                pool,
                build_symbol_table,
                self.files,
                self.codebase_root / self.codebase_name,
            )
        return TaskResult(
            data=file_to_symbols, serialization=SerializationMethod.PICKLE
        )

    @property
    def work_units(self) -> int:
        return TaskWorkUnits.SYMBOL_TABLE

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        import os

        import boto3
        from shared.inspector.utils.io import upload_symbol_table_to_s3

        symbol_table = task_result.data
        s3_client = boto3.client(
            "s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL")
        )
        bucket_name = os.environ["INSPECTOR_BUCKET_NAME"]

        upload_symbol_table_to_s3(
            symbol_table=symbol_table,
            s3_client=s3_client,
            bucket_name=bucket_name,
            version_id=self.version_id,
        )
        return {}
