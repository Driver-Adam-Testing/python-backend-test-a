import asyncio
import itertools
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Any, ClassVar, Self
from uuid import UUID

import tiktoken
import toml
from aiolimiter import AsyncLimiter
from chat_openai import ChatOpenAI
from database.models_enums import ContentKind, NodeKind
from logger import logger
from prompts import (
    _USER_CONTEXT_SIZE_MAP,
    NO_CONTENT_FOUND_RESPONSE,
    USER_CONTEXT_BASE,
    append_system_prompt,
    append_user_prompt,
    generate_system_prompt,
    generate_user_prompt,
    summary_system_prompt,
    summary_user_prompt,
)
from shared.chunking.text_splitter import split_text
from shared.prompts.structured_prompting import (
    Prompt,
)
from sqlalchemy import func
from sqlmodel import or_, select
from tqdm.asyncio import tqdm_asyncio


@dataclass
class AutoToml:
    @dataclass
    class NodeInfo:
        id: str
        relative_path: str
        version_id: str

    @dataclass(frozen=True)
    class SourceStats:
        pdf_page_ct: int
        source_file_ct: int
        directory_ct: int
        codebase_file_nodes: list["AutoToml.NodeInfo"]
        pdf_nodes: list["AutoToml.NodeInfo"]
        directory_nodes: list["AutoToml.NodeInfo"]

    class ScaleMode(Enum):
        NONE = 1
        SCALE_PDFS = 2
        SCALE_PDF_AND_CODE = 3
        SCALE_PDF_AND_USE_DIRS = 4
        FAIL = 5

    LLM_SCATTER_MODEL: ClassVar[str] = (
        "o3-mini"  # Due to issues with 4.1 and 4o repeating content, o3-mini used for this stage
    )
    LLM_TOML_MODEL: ClassVar[str] = "gpt-5"

    MAX_CONCURRENT_SUMMARIES: ClassVar[int] = 300
    OPENAI_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_SUMMARIES)
    SCALING_THRESHOLD: ClassVar[int] = MAX_CONCURRENT_SUMMARIES * 0.5
    REQUESTS_PER_SECOND: ClassVar[int] = 100
    OPENAI_LIMITER = AsyncLimiter(REQUESTS_PER_SECOND, 1)
    MAX_CODE_SCALE_FACTOR: ClassVar[int] = 10
    PDF_SCALE_FACTOR: ClassVar[int] = 10
    MIN_FILE_COUNT_THRESHOLD_FOR_USE_DIRS: ClassVar[int] = 30

    node_ids: list[str]
    enable_auto_scaling: bool
    llm_scatter: ChatOpenAI
    llm_toml: ChatOpenAI
    code_contents: list[dict[str, str]]
    pdf_contents: list[dict[str, str]]

    @classmethod
    def from_node_ids(cls, node_ids: list[str], enable_auto_scaling: bool) -> Self:
        return cls._initialize(
            node_ids=node_ids, enable_auto_scaling=enable_auto_scaling
        )

    @classmethod
    def from_page_id(cls, page_id: UUID, enable_auto_scaling: bool) -> Self:
        from database.db import get_session
        from database.models import DocumentSource

        logger.info(f"Fetching document sources for page ID: {page_id}\n")
        with get_session() as session:
            document_sources = session.exec(
                select(DocumentSource).where(DocumentSource.page_node_id == page_id)
            ).all()

            if not document_sources:
                raise ValueError(f"No document sources found for page ID: {page_id}")
            node_ids = [str(source.source_node_id) for source in document_sources]

        return cls._initialize(
            node_ids=node_ids, enable_auto_scaling=enable_auto_scaling
        )

    @classmethod
    def from_root_node_id(cls, root_node_id: UUID, enable_auto_scaling: bool) -> Self:
        return cls._initialize(
            node_ids=[root_node_id], enable_auto_scaling=enable_auto_scaling
        )

    async def generate(self, document_goal: str, user_context: str = "") -> str:
        logger.info(f"Generating TOML from document goal:\n\n{document_goal}\n")

        logger.info(f"Additional user context:\n\n{user_context}\n")

        logger.info(
            f"Gathering summaries from {len(self.code_contents)} source files/directories and {len(self.pdf_contents)} PDF pages...\n"
        )

        if user_context in _USER_CONTEXT_SIZE_MAP:
            user_context = (
                Prompt.empty()
                .append(_USER_CONTEXT_SIZE_MAP.get(user_context, USER_CONTEXT_BASE))
                .into_str()
            )

        source_summary = await self._gather_summaries(
            document_goal=document_goal,
            user_context=user_context,
            source_contents=itertools.chain(self.code_contents, self.pdf_contents),
        )

        # logger.debug(f"{source_summary}\n")

        system_prompt = generate_system_prompt()
        user_prompt = generate_user_prompt(
            document_goal=document_goal,
            user_context=user_context,
            source_summary=source_summary,
        )

        # logger.info("Generating new TOML sections...\n")
        print(f"user_context: {user_context}")
        generated_toml_sections = await self.llm_toml.generate_response(
            system_prompt=system_prompt, user_prompt=user_prompt
        )

        document_section = {"document": {"goal": document_goal}}
        sanitized_document_section = toml.dumps(document_section)
        output = sanitized_document_section + "\n" + generated_toml_sections

        logger.debug(f"{output}")

        return output

    async def append(self, user_toml: str, user_context: str = "") -> str:
        logger.debug(f"Appending user supplied TOML:\n\n{user_toml}\n")

        logger.info(f"Additional user context:\n\n{user_context}\n")

        user_toml_parsed = toml.loads(user_toml)
        toml_sections = self._isolate_sections(user_toml_parsed)
        document_goal = user_toml_parsed.get("document", {}).get("goal", None)

        logger.info(
            f"Gathering summaries from {len(self.code_contents)} source files and {len(self.pdf_contents)} PDF pages...\n"
        )
        source_summary = await self._gather_summaries(
            document_goal=document_goal,
            user_context=user_context,
            source_contents=itertools.chain(self.code_contents, self.pdf_contents),
        )

        logger.debug(f"{source_summary}\n")

        system_prompt = append_system_prompt()
        user_prompt = append_user_prompt(
            document_goal=document_goal,
            user_context=user_context,
            source_summary=source_summary,
            user_toml=toml_sections,
        )

        logger.info("Generating additional TOML sections...\n")
        generated_toml_sections = await self.llm_toml.generate_response(
            system_prompt=system_prompt, user_prompt=user_prompt
        )

        output = user_toml + "\n\n" + generated_toml_sections

        logger.debug(f"{output}")

        return output

    async def _gather_summaries(
        self,
        document_goal: str,
        user_context: str,
        source_contents: Iterable[dict[str, str]],
    ) -> str:
        tasks = []
        for source_content in source_contents:
            path = next(iter(source_content.keys()))
            content = source_content[path]

            tasks.append(
                self._generate_summary(
                    path=path,
                    system_prompt=summary_system_prompt(),
                    user_prompt=summary_user_prompt(
                        document_goal=document_goal,
                        user_context=user_context,
                        source_content=content,
                    ),
                )
            )

        summaries = await tqdm_asyncio.gather(*tasks)

        summary = "\n\n".join(result.strip() for result in summaries if result.strip())

        print("Summary length before truncation:")
        print(len(summary))
        # new_summary = self._truncate_text(text=summary, llm=self.llm_toml)

        chunks = split_text(
            summary, chunk_size=64_000, chunk_overlap=6_400
        )  # Using 64k chunks since the "breakdown" point for larger context models is still unknown.
        new_summary = summary
        if len(chunks) > 1:
            print("Compressing summary...")
            new_summary = ""
            chunk_tasks = []
            for i, chunk in enumerate(chunks):
                chunk_tasks.append(
                    self._generate_summary(
                        path=f"Chunk {i + 1}",
                        system_prompt=summary_system_prompt(),
                        user_prompt=summary_user_prompt(
                            document_goal=document_goal,
                            user_context=user_context,
                            source_content=chunk.text,
                        ),
                    )
                )
            new_summaries = await tqdm_asyncio.gather(*chunk_tasks)
            new_summary = "\n\n".join(
                result.strip() for result in new_summaries if result.strip()
            )
        print("Summary length after compression:")
        print(len(new_summary))

        if new_summary is not summary:
            logger.error("Compressed content summary to fit within token limits\n")
            summary = new_summary

        return summary

    async def _generate_summary(
        self, path: str, system_prompt: str, user_prompt: str
    ) -> str:
        async with (
            self.OPENAI_SEMAPHORE,
            self.OPENAI_LIMITER,
        ):
            try:
                summary = await self.llm_scatter.generate_response(
                    system_prompt=system_prompt, user_prompt=user_prompt
                )
                if NO_CONTENT_FOUND_RESPONSE in summary:
                    # logger.debug(f"No relevant content found in:\n{path}")
                    return ""
                else:
                    return f"{path}\n\n{summary}"
            except Exception as e:
                logger.exception(f"{e!r} while generating summary for:\n{path}")
                raise

    def _isolate_sections(self, toml_content: dict[str, Any]) -> str:
        KEYS_TO_KEEP = ["title", "level", "instruction", "content_structure"]

        if "substitutions" in toml_content:
            mapping = {
                item["key"]: item["value"] for item in toml_content["substitutions"]
            }
        else:
            mapping = None

        sections = toml_content.get("sections", [])
        for section in sections:
            if mapping:
                if isinstance(section.get("instruction"), str):
                    try:
                        section["instruction"] = section["instruction"].format_map(
                            mapping
                        )
                    except KeyError as e:
                        logger.warning(f"Warning: Missing substitution key {e}")

                if isinstance(section.get("content_structure"), str):
                    try:
                        section["content_structure"] = section[
                            "content_structure"
                        ].format_map(mapping)
                    except KeyError as e:
                        logger.warning(f"Warning: Missing substitution key {e}")

            for key in list(section.keys()):
                if key not in KEYS_TO_KEEP:
                    section.pop(key, None)

        return toml.dumps({"sections": sections})

    @classmethod
    def _initialize(cls, node_ids: list[str], enable_auto_scaling: bool) -> Self:
        llm_scatter = ChatOpenAI(
            model=cls.LLM_SCATTER_MODEL,
            temperature=0.0,
            request_timeout=60 * 5,
        )
        llm_toml = ChatOpenAI(
            model=cls.LLM_TOML_MODEL,
            temperature=0.0,
            request_timeout=60 * 5,
        )
        stats = cls._get_source_stats(node_ids=node_ids)
        if enable_auto_scaling:
            scale_mode, code_scale_factor = cls._get_scale_mode_and_factor(stats=stats)
        else:
            scale_mode = cls.ScaleMode.NONE
            code_scale_factor = None

        logger.info(f"Collecting content for nodes:\n{'\n'.join(node_ids)}\n")

        code_content, pdf_content = cls._get_content_and_apply_scaling(
            stats=stats,
            scale_mode=scale_mode,
            code_scale_factor=code_scale_factor,
        )

        return cls(
            node_ids=node_ids,
            enable_auto_scaling=enable_auto_scaling,
            llm_scatter=llm_scatter,
            llm_toml=llm_toml,
            code_contents=code_content,
            pdf_contents=pdf_content,
        )

    @classmethod
    def _get_content_and_apply_scaling(
        cls,
        stats: SourceStats,
        scale_mode: ScaleMode,
        code_scale_factor: int | None,
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        match scale_mode:
            case cls.ScaleMode.NONE:
                code_contents, pdf_contents = cls._get_file_and_pdf_content(stats=stats)
            case cls.ScaleMode.SCALE_PDFS:
                code_contents, pdf_contents = cls._get_file_and_pdf_content(stats=stats)
                logger.info(
                    f"Scaling down PDF content from {stats.pdf_page_ct} pages by factor of {cls.PDF_SCALE_FACTOR}\n"
                )
                pdf_contents = cls._scale_contents(
                    contents=pdf_contents, scale_factor=cls.PDF_SCALE_FACTOR
                )
            case cls.ScaleMode.SCALE_PDF_AND_CODE:
                code_contents, pdf_contents = cls._get_file_and_pdf_content(stats=stats)
                logger.info(
                    f"Scaling down PDF content from {stats.pdf_page_ct} pages by factor of {cls.PDF_SCALE_FACTOR}\n"
                )
                pdf_contents = cls._scale_contents(
                    contents=pdf_contents, scale_factor=cls.PDF_SCALE_FACTOR
                )
                logger.info(
                    f"Scaling down code content from {stats.source_file_ct} files by factor of {code_scale_factor}\n"
                )
                code_contents = cls._scale_contents(
                    contents=code_contents, scale_factor=code_scale_factor
                )
            case cls.ScaleMode.SCALE_PDF_AND_USE_DIRS | cls.ScaleMode.FAIL:
                code_contents, pdf_contents = cls._get_directory_and_pdf_content(
                    stats=stats
                )
                logger.info(
                    f"Scaling down PDF content from {stats.pdf_page_ct} pages by factor of {cls.PDF_SCALE_FACTOR}\n"
                )
                pdf_contents = cls._scale_contents(
                    contents=pdf_contents, scale_factor=cls.PDF_SCALE_FACTOR
                )
                logger.info(
                    f"Using {stats.directory_ct} directory contents instead of {stats.source_file_ct} source code files\n"
                )
                if scale_mode == cls.ScaleMode.FAIL:
                    logger.warning(
                        "Auto-scaling failed. Too many sources to summarize.  Falling back on using directory contents only."
                    )

        return code_contents, pdf_contents

    @classmethod
    def _get_scale_mode_and_factor(cls, stats: SourceStats) -> tuple[ScaleMode, int]:
        mode = cls.ScaleMode.NONE
        code_scale_factor = 1
        pdf_page_ct = stats.pdf_page_ct
        source_file_ct = stats.source_file_ct
        directory_ct = stats.directory_ct

        source_ct = source_file_ct + pdf_page_ct

        if source_ct > cls.SCALING_THRESHOLD:
            mode = cls.ScaleMode.SCALE_PDFS
            pdf_page_ct //= cls.PDF_SCALE_FACTOR
            source_ct = source_file_ct + pdf_page_ct

            if (
                source_file_ct > cls.SCALING_THRESHOLD
                and pdf_page_ct < cls.SCALING_THRESHOLD
            ):
                code_scale_factor = ceil(
                    source_file_ct / (cls.SCALING_THRESHOLD - pdf_page_ct)
                )
                if (
                    code_scale_factor <= cls.MAX_CODE_SCALE_FACTOR
                    and (source_file_ct // code_scale_factor + pdf_page_ct)
                    <= cls.SCALING_THRESHOLD
                ):
                    mode = cls.ScaleMode.SCALE_PDF_AND_CODE
                    source_file_ct //= code_scale_factor
                    source_ct = source_file_ct + pdf_page_ct
                elif stats.directory_ct > 0:
                    mode = cls.ScaleMode.SCALE_PDF_AND_USE_DIRS
                    source_ct = stats.directory_ct + pdf_page_ct + source_file_ct
        if source_ct > cls.SCALING_THRESHOLD:
            mode = cls.ScaleMode.FAIL

        # TODO: redesign the logic to be built around dirs by default.
        # Blanket use of using directories by default, unless below a critical file
        # count threshold in scope. In that case, no scaling applied to code but
        # keep PDF scaling.
        mode = (
            cls.ScaleMode.SCALE_PDFS
            if (
                directory_ct == 0
                or source_file_ct <= cls.MIN_FILE_COUNT_THRESHOLD_FOR_USE_DIRS
            )
            else cls.ScaleMode.SCALE_PDF_AND_USE_DIRS
        )
        return mode, code_scale_factor

    @classmethod
    def _get_source_stats(cls, node_ids: list[str]) -> SourceStats:
        from database.db import get_session
        from database.models import DerivedContent, Node

        with get_session() as session:
            nodes_query = select(Node).where(Node.id.in_(node_ids))
            nodes = session.exec(nodes_query).all()

            codebase_file_nodes = []
            pdf_nodes = []
            directory_nodes = []

            for node in nodes:
                node_info = cls.NodeInfo(
                    id=node.id,
                    relative_path=node.relative_path,
                    version_id=node.version_id,
                )
                if node.kind == NodeKind.CODEBASE_FILE:
                    codebase_file_nodes.append(node_info)
                elif node.kind == NodeKind.OTHER:
                    pdf_nodes.append(node_info)
                elif node.kind == NodeKind.CODEBASE_DIRECTORY:
                    directory_nodes.append(node_info)

            pdf_page_ct = 0
            if pdf_nodes:
                pdf_node_ids = [node.id for node in pdf_nodes]
                pdf_page_ct = (
                    session.scalar(
                        select(func.count(DerivedContent.id)).where(
                            DerivedContent.node_id.in_(pdf_node_ids),
                            DerivedContent.content_kind
                            == ContentKind.PDF_EXTRACTED_TEXT,
                        )
                    )
                    or 0
                )

            source_file_ct = 0
            directory_ct = 0

            if codebase_file_nodes:
                codebase_node_ids = [node.id for node in codebase_file_nodes]
                source_file_ct += (
                    session.scalar(
                        select(func.count(DerivedContent.id)).where(
                            DerivedContent.node_id.in_(codebase_node_ids),
                            DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION,
                        )
                    )
                    or 0
                )

            if directory_nodes:
                path_conditions = cls._build_path_conditions(directory_nodes)

                source_file_ct += (
                    session.scalar(
                        select(func.count(DerivedContent.id))
                        .join(Node)
                        .where(
                            Node.kind == NodeKind.CODEBASE_FILE,
                            DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION,
                            or_(*path_conditions),
                        )
                    )
                    or 0
                )

                directory_ct = (
                    session.scalar(
                        select(func.count(DerivedContent.id))
                        .join(Node)
                        .where(
                            Node.kind == NodeKind.CODEBASE_DIRECTORY,
                            DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION,
                            or_(*path_conditions),
                        )
                    )
                    or 0
                )

        return cls.SourceStats(
            pdf_page_ct=pdf_page_ct,
            source_file_ct=source_file_ct,
            directory_ct=directory_ct,
            codebase_file_nodes=codebase_file_nodes,
            pdf_nodes=pdf_nodes,
            directory_nodes=directory_nodes,
        )

    @classmethod
    def _build_path_conditions(cls, directory_nodes: list["AutoToml.NodeInfo"]) -> list:
        from database.models import Node

        path_conditions = []
        for dir_node in directory_nodes:
            path_conditions.append(
                (Node.version_id == dir_node.version_id)
                & (Node.relative_path.like(f"{dir_node.relative_path}%"))
            )
        return path_conditions

    @classmethod
    def _get_file_and_pdf_content(
        cls, stats: SourceStats
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        from database.db import get_session
        from database.models import DerivedContent, Node

        with get_session() as session:
            code_contents = []
            pdf_contents = []

            if stats.codebase_file_nodes or stats.pdf_nodes:
                all_direct_node_ids = [
                    node.id
                    for node in itertools.chain(
                        stats.codebase_file_nodes, stats.pdf_nodes
                    )
                ]

                query = select(DerivedContent).where(
                    DerivedContent.node_id.in_(all_direct_node_ids),
                    DerivedContent.content_kind.in_(
                        [ContentKind.LONG_DESCRIPTION, ContentKind.PDF_EXTRACTED_TEXT]
                    ),
                )
                query_results = session.exec(query).all()

                node_lookup = {}
                for node in stats.codebase_file_nodes:
                    node_lookup[node.id] = (node.relative_path, False)
                for node in stats.pdf_nodes:
                    node_lookup[node.id] = (node.relative_path, True)

                for dc in query_results:
                    if dc.content is None:
                        continue

                    relative_path, is_pdf = node_lookup[dc.node_id]
                    content_dict = {relative_path: dc.content}

                    if is_pdf:
                        pdf_contents.append(content_dict)
                    else:
                        code_contents.append(content_dict)

            if stats.directory_nodes:
                path_conditions = cls._build_path_conditions(stats.directory_nodes)

                query = (
                    select(DerivedContent, Node)
                    .join(Node)
                    .where(
                        Node.kind == NodeKind.CODEBASE_FILE,
                        DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION,
                        or_(*path_conditions),
                    )
                )
                query_results = session.exec(query).all()
                code_contents.extend(
                    [
                        {node.relative_path: dc.content}
                        for dc, node in query_results
                        if dc.content is not None
                    ]
                )

            if not code_contents and not pdf_contents:
                all_node_ids = []
                if stats.codebase_file_nodes:
                    all_node_ids.extend([n.id for n in stats.codebase_file_nodes])
                if stats.pdf_nodes:
                    all_node_ids.extend([n.id for n in stats.pdf_nodes])
                if stats.directory_nodes:
                    all_node_ids.extend([n.id for n in stats.directory_nodes])
                raise ValueError(
                    f"No content found for the provided nodes: {all_node_ids}"
                )

            return code_contents, pdf_contents

    @classmethod
    def _get_directory_and_pdf_content(
        cls, stats: SourceStats
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        from database.db import get_session
        from database.models import DerivedContent, Node

        with get_session() as session:
            pdf_nodes = stats.pdf_nodes or []
            directory_nodes = stats.directory_nodes or []

            directory_contents = []
            pdf_contents = []

            if pdf_nodes:
                pdf_node_ids = [node.id for node in pdf_nodes]
                query = select(DerivedContent).where(
                    DerivedContent.node_id.in_(pdf_node_ids),
                    DerivedContent.content_kind == ContentKind.PDF_EXTRACTED_TEXT,
                )
                query_results = session.exec(query).all()

                pdf_path_lookup = {node.id: node.relative_path for node in pdf_nodes}
                pdf_contents = [
                    {pdf_path_lookup[dc.node_id]: dc.content}
                    for dc in query_results
                    if dc.content is not None
                ]

            if directory_nodes:
                path_conditions = cls._build_path_conditions(directory_nodes)

                query = (
                    select(DerivedContent, Node)
                    .join(Node)
                    .where(
                        Node.kind == NodeKind.CODEBASE_DIRECTORY,
                        DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION,
                        or_(*path_conditions),
                    )
                )
                query_results = session.exec(query).all()
                directory_contents.extend(
                    [
                        {node.relative_path: dc.content}
                        for dc, node in query_results
                        if dc.content is not None
                    ]
                )

            if not directory_contents and not pdf_contents:
                all_node_ids = []
                if stats.pdf_nodes:
                    all_node_ids.extend([n.id for n in stats.pdf_nodes])
                if stats.directory_nodes:
                    all_node_ids.extend([n.id for n in stats.directory_nodes])
                raise ValueError(
                    f"No content found for the provided nodes: {all_node_ids}"
                )

            return directory_contents, pdf_contents

    @classmethod
    def _truncate_text(
        cls, text: str, llm: ChatOpenAI | None, scale_factor: int = 1
    ) -> str:
        encoder = tiktoken.encoding_for_model(
            "gpt-4o"
            if llm and llm.model in ["gpt-4.1", "o3-mini"]
            else cls.LLM_SCATTER_MODEL
        )
        max_tokens = int(
            (
                ChatOpenAI.get_token_limit(llm.model if llm else cls.LLM_SCATTER_MODEL)
                * 0.7
            )
            // scale_factor
        )

        tokens = encoder.encode(text, disallowed_special=())
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[:max_tokens]
            text = encoder.decode(truncated_tokens)

        return text

    @classmethod
    def _scale_contents(
        cls, contents: list[dict[str, str]], scale_factor: int
    ) -> list[dict[str, str]]:
        scaled_contents = []
        for i in range(0, len(contents), scale_factor):
            sub_contents = contents[i : i + scale_factor]

            keys = [next(iter(content.keys())) for content in sub_contents]
            values = [next(iter(content.values())) for content in sub_contents]

            for idx, value in enumerate(values):
                new_value = cls._truncate_text(text=value, scale_factor=scale_factor)
                if new_value is not value:
                    values[idx] = new_value
                    logger.warning(f"Truncated content for: {keys[idx]}\n")

            key = "\n".join(keys)
            value = "\n".join(values)

            scaled_contents.append({key: value})
        return scaled_contents
