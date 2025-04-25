import argparse
import asyncio
import copy
import hashlib
import json
import os
import tempfile
import tomllib
from collections.abc import Generator
from enum import IntEnum, StrEnum
from graphlib import TopologicalSorter
from pathlib import Path
from typing import Any, Self

import boto3
import fitz
import openai
import pymupdf4llm
from database.models_v2_enums import AutoDocStatusMessageKind, ContentKind
from google import genai
from pydantic import BaseModel
from rich.console import Console
from rich.markdown import Markdown
from shared.chunking.text_splitter import get_num_tokens, split_text
from tqdm.asyncio import tqdm_asyncio
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind

try:
    with open("local_setup.json") as f:
        LOCAL_FILES: dict[str, str] = json.load(f)
except FileNotFoundError:
    LOCAL_FILES = None

OPENAI_SEM = asyncio.Semaphore(1000)
PDF_DOWNLOAD_DIR = "pdfs/"


async def llm_generate(llm: ChatOpenAI, system_prompt: str, user_prompt: str) -> str:
    async with OPENAI_SEM:
        try:
            return await llm.generate_response(
                system_prompt=system_prompt, user_prompt=user_prompt
            )
        except openai.BadRequestError:
            print(f"Bad request error for {user_prompt[:1000]}")
            return ""


GREEN = "\033[92m"  # Green
RED = "\033[91m"  # Red
CYAN = "\033[96m"  # Cyan
BLUE = "\033[94m"  # Blue
ORANGE = "\033[38;5;214m"  # Orange
RESET = "\033[0m"  # Reset color to default


class Category(IntEnum):
    HighlyRelevant = 0
    SomewhatRelevant = 1
    Irrelevant = 2

    @classmethod
    def from_str(cls, s: str) -> Self:
        return cls(int(s))


class ExecutionMode(StrEnum):
    LOCAL = "local"
    MODAL = "modal"


class NamedFlag(BaseModel):
    index: int
    name: str
    flag: bool


class SectionFlags(BaseModel):
    sections: list[NamedFlag]

    @classmethod
    async def from_llm(
        cls,
        llm: ChatOpenAI,
        goal: str,
        preamble: str,
        optional_sections: list[tuple[str, str, str]],
        long_descriptions: str,
    ) -> Self:
        system_prompt_template = """
You are an expert engineer and technical writer that specializes in documenting software.

Your job is to review the long description of source code provided to you and decide if certain topics are relevant or not. Specifically, we are considering if certain sections are relevant and should be included in a document we are writing to describe some code. Here is a description of the goal of the document we are wrting:

{goal}
{preamble_content}

The optional sections we are considering are described are listed below with the format <section index> <section name>: <description of section>:

{optional_section_descriptions}

Your job is to decide if these sections are relevant or not looking by considering descriptions of the code that will be provided to you. You return your decisions in a list, with the index, section name, and your decision for that section name (as a boolean value, where true indicates the section should be included and false indicates the section should not be included), provided for each section. The index is provided because it is possible for there to be more than one section with the same name, wherein the index as well as the description will differentiate them. Make sure the order, index, and section name in your output list matches the order provided to you as input.
"""
        user_prompt = f"Here is a collection of long descriptions for files and folders associated with the code. This is the context for you to decide if the optional sections are relevant:\n\n{long_descriptions}"
        preamble_content = (
            f"\nHere is further context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )

        optional_section_descriptions = ""
        for idx, _level, name, desc in optional_sections:
            optional_section_descriptions += f"- {idx} {name}: {desc}\n"
        system_prompt = system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            optional_section_descriptions=optional_section_descriptions,
        )

        return cls.model_validate_json(
            await llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
            )
        )


def _get_path_on_disk(codebase_name: str) -> Path:
    return Path(LOCAL_FILES[codebase_name]["abs_path_of_root_loc"]) / (
        codebase_name + ".json"
    )


def _get_pdf_paths(pdf_names: list[str], execution_mode: ExecutionMode) -> Path:
    match execution_mode:
        case ExecutionMode.LOCAL:
            pdf_paths = [
                Path(LOCAL_FILES[p]["abs_path_of_root_loc"]) / p for p in pdf_names
            ]
        case ExecutionMode.MODAL:
            pdf_paths = [Path(PDF_DOWNLOAD_DIR) / p for p in pdf_names]

    return pdf_paths


def _get_target_name(path: str) -> str:
    return Path(path).name


def _get_codebase_name(path: str) -> str:
    for p in Path(path).parts:
        if p != os.sep:
            return p

    raise ValueError(f"Could not construct codebase name for path: `{path}`")


async def update_autodocs_status(
    page_id: str, status_kind: AutoDocStatusMessageKind, content: str
) -> None:
    import modal
    from database.db import async_engine
    from database.models_v2 import AutoDocStatusHistory
    from sqlmodel.ext.asyncio.session import AsyncSession

    call_id = modal.current_function_call_id()

    async with AsyncSession(async_engine) as session, session.begin():
        status_update = AutoDocStatusHistory(
            page_node_id=page_id,
            status_kind=status_kind,
            content=content,
            call_id=call_id,
        )
        session.add(status_update)
        await session.commit()


async def get_autodoc_elapsed_time(page_id: str) -> float:
    import modal
    from database.db import async_engine
    from database.models_v2 import AutoDocStatusHistory
    from sqlmodel import select
    from sqlmodel.ext.asyncio.session import AsyncSession

    call_id = modal.current_function_call_id()

    async with AsyncSession(async_engine) as session:
        states = (
            await session.exec(
                select(AutoDocStatusHistory)
                .where(
                    AutoDocStatusHistory.page_node_id == page_id,
                    AutoDocStatusHistory.call_id == call_id,
                )
                .order_by(AutoDocStatusHistory.created_at.asc())
            )
        ).all()
        start_state = states[0]
        end_state = states[-1]
        elapsed_time = end_state.created_at - start_state.created_at
    return elapsed_time.total_seconds()


class TechDocsContent(BaseModel):
    name: str
    source: str | None
    short_sentence_description: str
    long_description: str
    short_paragraph_description: str


class DriverDocsContent(BaseModel):
    codebase_name: str
    version_id: str
    dag: dict[str, set[str]]
    content: dict[str, TechDocsContent]
    topo_order: list[str]

    def to_disk(self, p: Path) -> None:
        as_json = self.model_dump_json()
        with open(p, "w") as f:
            f.write(as_json)

    @classmethod
    def from_disk(cls, p: Path) -> Self:
        with open(p) as f:
            json_raw = f.read()

        return cls.model_validate_json(json_raw)

    @classmethod
    def from_db(cls, version_id: str, relative_path: str) -> Self:
        from database.db import get_session
        from database.models_v2 import Version
        from database.models_v2_enums import ContentKind
        from sqlalchemy.orm import selectinload
        from sqlmodel import select

        with get_session() as session:
            version = session.exec(
                select(Version)
                .where(Version.id == version_id)
                .options(selectinload(Version.primary_asset))
            ).first()
            codebase_name = version.primary_asset.display_name
            primary_asset_id = version.primary_asset_id
            organization_id = version.primary_asset.organization_id
        bucket = hashlib.sha256(organization_id.encode()).hexdigest()[:63]

        ss = _get_derived_contents(
            version_id=version_id,
            relative_path=relative_path,
            dc_kind=ContentKind.SHORT_SENTENCE_DESCRIPTION,
        )
        ld = _get_derived_contents(
            version_id=version_id,
            relative_path=relative_path,
            dc_kind=ContentKind.LONG_DESCRIPTION,
        )
        sp = _get_derived_contents(
            version_id=version_id,
            relative_path=relative_path,
            dc_kind=ContentKind.SHORT_PARAGRAPH_DESCRIPTION,
        )
        # TODO: this will download everything right now, vs. just the subgraph of interest
        with tempfile.TemporaryDirectory() as download_dir:
            try:
                content = {
                    k: TechDocsContent(
                        name=k,
                        source=_get_source_from_s3(
                            version_id, primary_asset_id, k, bucket, download_dir
                        ),
                        short_sentence_description=ss[k],
                        long_description=ld[k],
                        short_paragraph_description=sp[k],
                    )
                    for k in ss
                }
            except Exception as e:
                print(codebase_name)
                raise e
            dag = build_file_tree_dag(
                codebase_name=codebase_name,
                content=content,
                codebase_root=download_dir,
                exeuction_mode=ExecutionMode.MODAL,
            )
            toposort = TopologicalSorter(dag)

        return DriverDocsContent(
            codebase_name=codebase_name,
            version_id=version_id,
            dag=dag,
            content=content,
            topo_order=list(toposort.static_order()),
        )

    def walk_topo(self) -> Generator[tuple[str, TechDocsContent], None, None]:
        return ((p, self.content[p]) for p in self.topo_order)


def _get_derived_contents(
    version_id: str, relative_path: str, dc_kind: ContentKind
) -> dict[str, str]:
    from database.db import get_session
    from database.models_v1 import DerivedContent
    from database.models_v2 import Node
    from sqlmodel import select

    with get_session() as session:
        dc_query = (
            select(DerivedContent)
            .join(Node)
            .where(
                Node.version_id == version_id,
                Node.relative_path.like(f"{relative_path}%"),
                DerivedContent.content_kind.in_([dc_kind]),
            )
        )
        derived_contents = session.exec(dc_query).all()
        return {dc.relative_path: dc.content for dc in derived_contents}


def _get_source_from_s3(
    version_id: str,
    primary_asset_id: str,
    relative_path: str,
    bucket: str,
    download_dir: str,
) -> str:
    try:
        s3_client = boto3.client("s3")
        download_key = f"{primary_asset_id}/{version_id}/{relative_path}"
        local_download_path = Path(download_dir) / relative_path
        local_download_path.parent.mkdir(parents=True, exist_ok=True)
        print(bucket, download_key)
        s3_client.download_file(bucket, download_key, str(local_download_path))

        with open(local_download_path) as f:
            return f.read()
    except Exception:
        return None


def _download_pdf_from_s3(version_id: str) -> str:
    from database.db import get_session
    from database.models_v2 import Node, Version
    from sqlalchemy.orm import selectinload
    from sqlmodel import select

    with get_session() as session:
        version = session.exec(
            select(Version)
            .where(Version.id == version_id)
            .options(selectinload(Version.primary_asset))
        ).first()
        primary_asset_id = version.primary_asset_id
        pdf_name = version.primary_asset.display_name
        organization_id = version.primary_asset.organization_id
        node = session.exec(select(Node).where(Node.version_id == version_id)).first()
    bucket = hashlib.sha256(organization_id.encode()).hexdigest()[:63]
    download_dir = Path(PDF_DOWNLOAD_DIR)
    download_dir.mkdir(exist_ok=True)
    local_download_path = download_dir / pdf_name

    s3_client = boto3.client("s3")
    download_key = f"{primary_asset_id}/{version_id}/{node.relative_path}"
    s3_client.download_file(bucket, download_key, str(local_download_path))


def build_file_tree_dag(
    codebase_name: str,
    content: dict[str, TechDocsContent],
    codebase_root: str | None,
    exeuction_mode: ExecutionMode,
) -> dict[str, set[str]]:
    if exeuction_mode == ExecutionMode.LOCAL and codebase_root is None:
        codebase_root = Path(LOCAL_FILES[codebase_name]["abs_path_of_root_loc"])
    elif codebase_root is not None:
        codebase_root = Path(codebase_root)
    included_nodes = {str(k) for k in content}
    dag = dict()

    for (
        local_root,
        dirs,
        files,
    ) in os.walk(codebase_root / codebase_name):
        children = set()
        for d in dirs:
            root_rel_path = str((Path(local_root) / d).relative_to(codebase_root))
            if root_rel_path in included_nodes:
                children.add(root_rel_path)
        for f in files:
            root_rel_path = str((Path(local_root) / f).relative_to(codebase_root))
            if root_rel_path in included_nodes:
                dag[root_rel_path] = set()
                children.add(root_rel_path)
        local_root_rel_path = str(Path(local_root).relative_to(codebase_root))
        if local_root_rel_path in included_nodes:
            dag[local_root_rel_path] = children

    return dag


def build_subgraph(dag: dict[str, set[str]], start: str) -> dict[str, set[str]]:
    if start not in dag:
        raise ValueError(f"Node {start} is not present in the DAG.")

    subgraph = dict()

    def dfs(node: str) -> None:
        if node in subgraph:
            # We've already visited this node.
            return
        # Add the node to the subgraph with a copy of its children.
        subgraph[node] = dag[node]
        for child in dag[node]:
            dfs(child)

    dfs(start)
    return subgraph


class DocKind(StrEnum):
    DEFINED_SECTIONS = "defined_sections"
    UNDEFINED = "undefined"
    FROM_EXAMPLE = "from_example"
    ARCHITECTURE = "architecture"


class SectionCreationMethod(StrEnum):
    SEQUENTIAL_EDIT = "sequential_edit"
    SCATTER_GATHER = "scatter_gather"
    ONLY_PDFS = "only_pdfs"
    CODE_EXAMPLE = "code_example"


class LlmCfg(BaseModel):
    tag_model: str
    section_init_model: str
    section_update_model: str
    section_format_model: str
    assembly_model: str
    copy_editor_model: str

    @classmethod
    def default(cls) -> Self:
        return cls(
            tag_model="gpt-4o",
            section_init_model="o3-mini",
            section_update_model="gpt-4o",
            section_format_model="o3-mini",
            assembly_model="o3-mini",
            copy_editor_model="gpt-4o",
        )


class DocumentCfg(BaseModel):
    goal: str
    fmt: DocKind
    use_tagging: bool
    config_name: str
    config_version: str


class FullyQualifiedDriverPathPdf(BaseModel):
    version_id: str
    pdf_name: str


class FullyQualifiedDriverPathCode(BaseModel):
    version_id: str
    node_path: str


class Scope(BaseModel):
    preamble: str
    pdfs: list[FullyQualifiedDriverPathPdf]
    code: list[FullyQualifiedDriverPathCode]

    @classmethod
    def default(cls) -> Self:
        return cls(
            preamble="",
            code=[],
            pdfs=[],
        )


class SectionCfg(BaseModel):
    title: str
    level: int
    required: bool = True  # this setting is ignored when committed_with is not None
    instruction: str
    content_structure: str
    section_creation_method: SectionCreationMethod
    committed_with: str = None


class SectionCommitted(BaseModel):
    title: str
    level: int
    instruction: str
    content_structure: str
    section_creation_method: SectionCreationMethod

    @classmethod
    def from_section_cfg(cls, cfg: SectionCfg) -> Self:
        return cls(
            title=cfg.title,
            level=cfg.level,
            instruction=cfg.instruction,
            content_structure=cfg.content_structure,
            section_creation_method=cfg.section_creation_method,
        )

    def annotation_system_prompt(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer that specializes in annotating files and folders of a codebase for their relevance to writing a specific section for a specific document.

The specific document being written has the following goal:

{goal}
{preamble_content}

The specific section of the document you are assessing relevance for has the following description:

{heading} {title}
{instruction}

Your job is to review source code provided to you and decide which of the following categories it belongs to:

**Highly Relevant**: This means the file contains critical information to write about this specific section.

**Somewhat Relevant**: This means the file contains some information needed to write about this specific section, but it is not necessarily critical.

**Irrelevant**: This means the file contains content that should not be considered when writing this section because it is not relevant. It is important to identify irrelevant content so we do not consider the wrong information or add noise into the process of writing the specific section of the specific document.

You will be given the source code for an entire file and will respond with a single number corresponding to the category you identify for the source code. Only output this single number:

- 0 for a Highly Relevant file
- 1 for a Somewhat Relevant file
- 2 for an Irrelevant file
        """
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def pdf_annotation_system_prompt(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer that specializes in annotating files and folders of a codebase for their relevance to writing a specific section for a specific document.

The specific document being written has the following goal:

{goal}
{preamble_content}

The specific section of the document you are assessing relevance for has the following description:

{heading} {title}
{instruction}

Your job is to review a page from a pdf provided to you and decide which of the following categories it belongs to:

**Highly Relevant**: This means the page contains critical information to write about this specific section.

**Somewhat Relevant**: This means the page contains some information needed to write about this specific section, but it is not necessarily critical.

**Irrelevant**: This means the page contains content that should not be considered when writing this section because it is not relevant. It is important to identify irrelevant content so we do not consider the wrong information or add noise into the process of writing the specific section of the specific document.

You will be given a single page from a pdf in markdown rendered text from and will respond with a single number corresponding to the category you identify for the source code. Only output this single number:

- 0 for a Highly Relevant file
- 1 for a Somewhat Relevant file
- 2 for an Irrelevant file
        """
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def init_draft_system_prompt_code(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to write an initial draft of one section in a larger document.

You will be given a high level description of the content in a codebase that you should use to write the content for you section. This high level description will pertain to one or more root folders and their immediate children or just a single file. This is a limited set of information.

The goal is to generate a starting point for the section of your document. In subsequent writing steps, others will refine this document based on your initial draft. Because you have limited information, the most valuable thing you can do is provide a good outline and structure. Fill in content for documents of the document as best you can, but focus on a solid structure with subsections that are most meaningful and relevant to the context given to you. For example, since you will not be looking at source code directly, you should not try and provide any source code examples.

The section you are writing about is titled {title}. Here is the a description of the kind of content you should include for the section:

{heading} {title}
{instruction}

Your output should be markdown formatted text including the section title as a top level header, important subsections, and content included for each subsection as appropriate.
        """
        preamble_content = (
            f"\nHere is further context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def init_draft_system_prompt_pdf(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to write a draft of a section in a larger document based on the content of the PDF.

The section you are writing about is titled {title}. Here is a description of the kind of content you should include in the section:

{heading} {title}
{instruction}

Here is a description of how your output should be formated:

{content_structure}

Your output should be markdown formatted text.
        """
        preamble_content = (
            f"\nHere is further context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
            content_structure=self.content_structure,
        )

    def update_from_file_system_prompt(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to take a current version of a section for a larger document that will be provided to you and update it, as appropriate, from details of a particular file that will also be provided to you. The contents follow Markdown syntax, which you will also follow in any updates you make. This is part of an iterative process wherein an initial, high level draft is updated with details from critical files and folders.

The details of the particular file will include a description of the contents of the file in human language as well as the source code.

Your job is to update the existing section content by editing or adding details based only on the content of the particular file provided. You will have access to the source code of just this one particular file, so you should focus on using this to add detail (descriptive, conceptual, technical) to the section content.

It is very important to add and include significant technical details from the source code. Here is a description of the section you are editing and instruction on what content should be in this section:

{heading} {title}
{instruction}

The details of this file may not provide information relevant to this section. If there are no clear and meaningful updates to make to the section draft based on the particular file contents, then do not make any edits.

Your output is the full content for the section of the document you have been provided with updates made based on your analysis of the particular file contents provided to you.

Your expected audience is a technical engineer.
        """
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def update_from_pdf_system_prompt(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to take a current version of a section for a larger document that will be provided to you and update it, as appropriate, from details of a particular page from a pdf that will also be provided to you. The contents follow Markdown syntax, which you will also follow in any updates you make. This is part of an iterative process wherein an initial, high level draft is updated with details from critical files and pdf pages.

You will be provided the pdf page as markdown rendered text.

Your job is to update the existing section content by editing or adding details based only on the content of the particular page provided.

It is very important to add and include any significant details from the page. Here is a description of the section you are editing and instruction on what content should be in this section:

{heading} {title}
{instruction}

The details of this pdf page may not provide information relevant to this section. If there are no clear and meaningful updates to make to the section draft based on the particular file contents, then do not make any edits.

Your output is the full content for the section of the document you have been provided with updates made based on your analysis of the particular file contents provided to you.

Your expected audience is a technical engineer.
        """
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def update_from_folder_system_prompt(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to take a current version of a section for a larger document that will be provided to you and update it, as appropriate, from details of a particular folder that will also be provided to you. The contents follow Markdown syntax, which you will also follow in any updates you make. This is part of an iterative process wherein an initial, high level draft is updated with details from critical files and folders.

The details of the particular folder will include a brief description of all of the child files and subfolders of the folder.

Your job is to update the existing section content by editing or adding details based only on the content of the particular folder provided. Since you will only have access to summary information (brief descriptions of all children of this folder), you should focus on higher level organization and structure to the section instead of modifying or adding technical details.

Here is a description of the section you are editing and instruction on what content should be in this section:

{heading} {title}
{instruction}

The details of this folder may not provide information relevant to this section. If there are no clear and meaningful updates to make to the section draft based on the particular folder contents, then do not make any edits.

Your output is the full content for the section of the document you have been provided with updates made based on your analysis of the particular folder contents provided to you.

Your expected audience is a technical engineer.
        """
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def final_output_format(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer, technical writer, and copy editor. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to write the final form of the {title} section for a document using Markdown syntax. You will be given detailed content for this section built up iteratively. Your job is to edit, rewrite, and reformat this content to conform to the following structure:

{heading} {title}
{content_structure}

Your output is the content of the section reformatted to fit the described content structure and your expected audience is a technical engineer.
        """
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            content_structure=self.content_structure,
        )

    def scatter_system_prompt(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to write a section a larger document through the lens of a relevant file, page from a pdf, or folder.

You will be given the source content from a single file or a page from a pdf identified to be relevant to the section. This is a limited set of information.

The goal is to write a version for the section of your document using just the context from this file.

The section you are writing about is titled {title}. Here is the a description of the kind of content you should include for the section:

{heading} {title}
{instruction}

Your output should be markdown formatted text including the section title as a top level header, important subsections, and content included for each subsection as appropriate.

Technical detail is very important in this document. As you write the document, cite specific examples from the source code or pdf page to support your documentation.

Use only content directly from the source code or pdf page to write the document. Do not make up any content that is not directly from the source code or pdf page.

It is okay to just return "no relevant content" if the source code or pdf page does not provide any relevant content for the section.
"""
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def gather_system_prompt(self, goal: str, preamble: str) -> str:
        aggregate_system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to write a section of a larger document.

You will be given many sections written about a set of files identified to be highly relevant to the section.

The goal is to generate the section by aggregating the information from these file specific sections.

The section you are writing is titled {title}. Here is the a description of the kind of content you should include for the section:

{heading} {title}
{instruction}

Your output should be a document with important sections/subsections using Markdown syntax with content included for each subsection as appropriate.

Technical detail is very important in this document. Try to keep as much technical detail from each file as possible, but combine and organize the information in a logical way.
"""
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return aggregate_system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def gather_multiple_system_prompt(self, goal: str, preamble: str) -> str:
        aggregate_system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to write a section of a larger document.

You will be given many sections written about aggregate sets of files identified to be highly relevant to the section.

The goal is to generate the section by aggregating the infromation from these aggregate file specific sections.

The section you are writing is titled {title}. Here is the a description of the kind of content you should include for the section:

{heading} {title}
{instruction}

Your output should be a document with important sections/subsections using Markdown syntax with content included for each subsection as appropriate.

Technical detail is very important in this document. Try to keep as much technical detail from each section as possible, but combine and organize the information in a logical way.
"""
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return aggregate_system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
        )

    def code_example_single_pass_system_prompt(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to write a draft a code example that will be used in a larger document based on the content of the code provided.

You will be provided source code of one or more source files deemed to be relevant to the code example you are constructing.

The section you are writing a code example for is titled: {title}. Here is a description of the kind of content you should include in the section:

{heading} {title}
{instruction}

Here is a description of how your output should be formated:

{content_structure}

Your output should be markdown formatted text.
        """
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
            content_structure=self.content_structure,
        )

    def code_example_single_pass_aggregate_pass(self, goal: str, preamble: str) -> str:
        system_prompt_template = """
You are an expert software engineer and technical writer. You specialize in writing documents with the following goal:

{goal}

Your job is to write a draft a code example that will be used in a larger document based on the content of the code provided.

You will be provided code examples generated using different files deemed to be relevant to the code example you are constructing.

Your goal is to combine these code examples into one coherent example that exemplifies the section you're writing a code example for: {title}.

Here is a description of the kind of content you should include in the section:

{heading} {title}
{instruction}

Here is a description of how your output should be formated:

{content_structure}

Your output should be markdown formatted text.
        """
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{preamble}"
            if preamble.strip() != ""
            else ""
        )
        heading = "#" * self.level
        return system_prompt_template.format(
            goal=goal,
            preamble_content=preamble_content,
            heading=heading,
            title=self.title,
            instruction=self.instruction,
            content_structure=self.content_structure,
        )

    async def code_example_few_shot_generator(
        self,
        document_goal: str,
        document_preamble: str,
        reverse_topos: list,
        tagged_nodes: dict[str, list[Category]] | None,
        tag_idx: int | None,
    ) -> str:
        llm = ChatOpenAI(model="o3-mini", temperature=0, request_timeout=300)
        # TODO: this is done naively - if we need to do this, we should keep related content together
        # could be useful to leverage symbol table here
        user_prompts = self.source_code_aggregation_user_prompt_constructor(
            reverse_topos=reverse_topos,
            annotations=tagged_nodes,
            tag_idx=tag_idx,
        )
        coroutines = []
        for user_prompt in user_prompts:
            coroutines.append(
                llm_generate(
                    llm=llm,
                    system_prompt=self.code_example_single_pass_system_prompt(
                        goal=document_goal, preamble=document_preamble
                    ),
                    user_prompt=user_prompt,
                )
            )
        responses = await asyncio.gather(*coroutines)

        # TODO: could be interesting to do a pass with the symbol table here, e.g.
        # identify the symbols used in the code examples and pass those in with the
        # generated code examples to keep some amount of context
        if len(responses) > 1:
            print(
                f"{self.title} requires aggregation of {len(responses)} code examples..."
            )
            aggregate_user_prompt = ""
            for idx, response in enumerate(responses):
                aggregate_user_prompt += (
                    f"Code example for set {idx}:\n\n{response}\n\n"
                )
            response = await llm_generate(
                llm=llm,
                system_prompt=self.code_example_single_pass_aggregate_pass(
                    goal=document_goal,
                    preamble=document_preamble,
                ),
                user_prompt=aggregate_user_prompt,
            )
            return response
        else:
            return responses[0]

    async def create_section_scatter_gather(
        self,
        goal: str,
        preamble: str,
        reverse_topos: list,
        pdf_paths: list | None,
        tagged_nodes: dict | None,
        pdf_tagged_nodes: dict | None,
        tag_idx: int | None,
        section_name: str,
    ) -> str:
        print(f"Creating node sections for {section_name}...")
        file_by_file_content = await self.create_node_sections(
            goal,
            preamble,
            reverse_topos,
            pdf_paths,
            tagged_nodes,
            pdf_tagged_nodes,
            tag_idx,
        )

        aggregate_docs = await self.aggregate_node_sections(
            goal,
            preamble,
            file_by_file_content,
            section_name,
        )

        while len(aggregate_docs) > 1:
            aggregate_docs = await self.aggregate_aggregate_sections(
                goal,
                preamble,
                aggregate_docs,
                section_name,
            )
        return aggregate_docs[0]

    async def create_node_sections(
        self,
        goal: str,
        preamble: str,
        reverse_topos: list,
        pdf_paths: list | None,
        tagged_nodes: dict | None,
        pdf_tagged_nodes: dict | None,
        tag_idx: int | None,
    ) -> dict:
        init_model = "o3-mini"
        llm = ChatOpenAI(model=init_model, request_timeout=500, temperature=0)

        file_by_file_content = {}
        node_coroutines = []
        ordered_nodes = []

        for reverse_topo in reverse_topos:
            root_p, root_content = reverse_topo[0]
            # Always force at least the root of every dag to be used to generate the section
            ordered_nodes.append(root_p)
            user_prompt = self.scatter_user_prompt_constructor(
                root_content, root_content, root_p
            )
            node_coroutines.append(
                llm_generate(
                    llm=llm,
                    system_prompt=self.scatter_system_prompt(goal, preamble),
                    user_prompt=user_prompt,
                )
            )
            for p, tech_docs in reverse_topo[1:]:
                # print(f"Generating node section for {p}...")
                if (
                    tag_idx is None
                    or tagged_nodes is None
                    or (
                        tagged_nodes[p][tag_idx] == Category.HighlyRelevant
                        or tagged_nodes[p][tag_idx] == Category.SomewhatRelevant
                    )
                ):
                    ordered_nodes.append(p)

                    user_prompt = self.scatter_user_prompt_constructor(
                        root_content, tech_docs, p
                    )
                    node_coroutines.append(
                        llm_generate(
                            llm=llm,
                            system_prompt=self.scatter_system_prompt(goal, preamble),
                            user_prompt=user_prompt,
                        )
                    )

        print("Generating node sections for pdfs...")
        for pdf_path in pdf_paths:
            with fitz.open(pdf_path) as doc:
                for idx, _ in enumerate(doc):
                    if (
                        pdf_tagged_nodes is None
                        or tag_idx is None
                        or pdf_tagged_nodes[pdf_path][idx][tag_idx]
                        == Category.HighlyRelevant
                    ):
                        ordered_nodes.append(str(pdf_path) + f" page {idx}")
                        md_text = pymupdf4llm.to_markdown(
                            pdf_path, pages=[idx], show_progress=False
                        )
                        user_prompt = f"Page content from {pdf_path}:\n\n{md_text}"
                        node_coroutines.append(
                            llm_generate(
                                llm=llm,
                                system_prompt=self.scatter_system_prompt(
                                    goal, preamble
                                ),
                                user_prompt=user_prompt,
                            )
                        )

        node_responses = await asyncio.gather(*node_coroutines)
        for ordered_node, response in zip(ordered_nodes, node_responses):
            file_by_file_content[ordered_node] = response

        print(f"Created {len(file_by_file_content)} node sections")
        return file_by_file_content

    async def aggregate_node_sections(
        self,
        goal: str,
        preamble: str,
        file_by_file_content: dict,
        section_name: str,
    ) -> list:
        model = "o3-mini"
        llm = ChatOpenAI(model=model, request_timeout=500, temperature=0)
        user_prompts = self.gather_user_prompt_constructor(
            file_by_file_content, section_name
        )

        aggregate_coroutines = []
        aggregate_docs = []

        for prompt in user_prompts:
            aggregate_coroutines.append(
                llm_generate(
                    llm=llm,
                    system_prompt=self.gather_system_prompt(goal, preamble),
                    user_prompt=prompt,
                )
            )
        print(
            f"Aggregating nodes with {len(aggregate_coroutines)} buckets for {section_name}"
        )
        aggregate_responses = await asyncio.gather(*aggregate_coroutines)
        for response in aggregate_responses:
            aggregate_docs.append(response)
        return aggregate_docs

    async def aggregate_aggregate_sections(
        self,
        goal: str,
        preamble: str,
        aggregate_docs: list,
        section_name: str,
    ) -> list:
        model = "o3-mini"
        llm = ChatOpenAI(model=model, request_timeout=500, temperature=0)
        user_prompts = self.gather_aggregate_user_prompt_constructor(
            aggregate_docs, section_name
        )
        aggregate_coroutines = []
        new_aggregate_docs = []
        for prompt in user_prompts:
            aggregate_coroutines.append(
                llm_generate(
                    llm=llm,
                    system_prompt=self.gather_multiple_system_prompt(goal, preamble),
                    user_prompt=prompt,
                )
            )
        print(
            f"Aggregating aggregates with {len(aggregate_coroutines)} buckets for {section_name}"
        )
        aggregate_responses = await asyncio.gather(*aggregate_coroutines)
        for response in aggregate_responses:
            new_aggregate_docs.append(response)
        return new_aggregate_docs

    def scatter_user_prompt_constructor(
        self,
        root_content: TechDocsContent,
        node_content: TechDocsContent,
        node_path: str,
    ) -> str:
        user_prompt = f"Short description of the full codebase:\n\n{root_content.short_paragraph_description}\n\n"
        user_prompt += (
            f"DESCRIPTION OF `{node_path}`:\n\n{node_content.long_description}\n\n"
        )
        # TODO: handle context window issues for both source code and long description
        if node_content.source is not None:
            if len(node_content.source.strip()) > 0:
                user_prompt += (
                    f"Source code for  `{node_path}`:\n\n{node_content.source}\n\n"
                )
            else:
                user_prompt += f"Source code for  `{node_path}`:\n\nEmpty file\n\n"
        chunks = split_text(user_prompt, chunk_size=96_000, chunk_overlap=0)
        if len(chunks) > 1:
            return chunks[0].text
        return user_prompt

    def source_code_aggregation_user_prompt_constructor(
        self,
        reverse_topos: list,
        annotations: dict[str, list[Category]] | None,
        tag_idx: int | None,
        chunk_size: int = 100_000,
    ) -> list:
        user_prompt = ""
        for reverse_topo in reverse_topos:
            for p, tech_docs in reverse_topo:
                if (
                    tag_idx is None
                    or annotations is None
                    or (annotations[p][tag_idx] == Category.HighlyRelevant)
                ) and tech_docs.source is not None:
                    user_prompt += (
                        f"Source code of file `{p}`:\n\n{tech_docs.source}\n\n"
                    )
        chunks_required = split_text(
            user_prompt, chunk_size=chunk_size, chunk_overlap=0
        )
        if len(chunks_required) > 1:
            num_tokens = get_num_tokens(user_prompt)
            token_threshold = num_tokens / len(chunks_required)
            user_prompts = [""]
            for reverse_topo in reverse_topos:
                for p, tech_docs in reverse_topo:
                    if (
                        tag_idx is None
                        or annotations is None
                        or (
                            annotations[p][tag_idx] == Category.HighlyRelevant
                            or annotations[p][tag_idx] == Category.SomewhatRelevant
                        )
                    ):
                        new_prompt = (
                            f"Source code of file `{p}`:\n\n{tech_docs.source}\n\n"
                        )
                        new_tokens = get_num_tokens(new_prompt)
                        found_prompt = False
                        for idx, prompt in reversed(list(enumerate(user_prompts))):
                            if new_tokens + get_num_tokens(prompt) > token_threshold:
                                pass
                            else:
                                user_prompts[idx] += new_prompt
                                found_prompt = True
                                break
                        if not found_prompt:
                            user_prompts.append(new_prompt)
        else:
            user_prompts = [user_prompt]

        return user_prompts

    def gather_user_prompt_constructor(
        self,
        file_by_file_content: dict,
        section_name: str,
    ) -> list:
        chunk_size = 64_000
        chunk_overlap = 0
        user_prompt = ""
        user_prompts = [""]
        for p, content in file_by_file_content.items():
            user_prompt += f"{section_name} of file or folder `{p}`:\n\n{content}\n\n"

        chunks_required = split_text(
            user_prompt, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        if len(chunks_required) > 1:
            num_tokens = get_num_tokens(user_prompt)
            token_threshold = num_tokens / len(chunks_required)
            user_prompts = [""]
            # print(f"Num Tokens: {num_tokens}. Token threshold: {token_threshold}")
            for p, content in file_by_file_content.items():
                new_prompt = f"{section_name} of file or folder `{p}`:\n\n{content}\n\n"
                new_tokens = get_num_tokens(new_prompt)
                found_prompt = False
                for idx, prompt in reversed(
                    list(enumerate(user_prompts))
                ):  # Reverse order to find most likely to be able to add to
                    if new_tokens + get_num_tokens(prompt) > token_threshold:
                        pass
                        # print(f"Prompt {idx} is too large to add to. Checking next")
                    else:
                        user_prompts[idx] += new_prompt
                        # print(f"Added {p} content to prompt {idx}")
                        found_prompt = True
                        break
                if not found_prompt:
                    user_prompts.append(new_prompt)
                    # print(f"Added {p} content to new prompt")
        else:
            user_prompts = [user_prompt]

        return user_prompts

    def gather_aggregate_user_prompt_constructor(
        self,
        aggregate_docs: list,
        section_name: str,
    ) -> list:
        # TODO: multiple prompt handling... That would be VERY large
        user_prompts = [""]
        for idx, doc in enumerate(aggregate_docs):
            user_prompts[0] += f"{section_name} doc for set {idx}:\n\n{doc}\n\n"
        return user_prompts


class AutoDocCfg(BaseModel):
    llm: LlmCfg
    document: DocumentCfg
    scope: Scope
    sections: list[SectionCfg]

    @classmethod
    def from_file(cls, toml_file: str) -> Self:
        with open(toml_file, "rb") as f:
            raw_data = tomllib.load(f)
        llm_raw_default = LlmCfg.default().model_dump()
        if "llm" in raw_data:
            raw_data["llm"] = {**llm_raw_default, **raw_data["llm"]}
        else:
            raw_data.setdefault("llm", llm_raw_default)

        scope_raw_default = Scope.default().model_dump()
        if "scope" in raw_data:
            raw_data["scope"] = {**scope_raw_default, **raw_data["scope"]}
        else:
            raw_data.setdefault("scope", scope_raw_default)
        raw_data.setdefault("sections", [])
        cfg = cls(**raw_data)
        if "substitutions" in raw_data:
            mapping = {item["key"]: item["value"] for item in raw_data["substitutions"]}
            for section in cfg.sections:
                section.instruction = section.instruction.format_map(mapping)
                section.content_structure = section.content_structure.format_map(
                    mapping
                )

        return cfg

    async def eval_optional_sections(
        self, llm: ChatOpenAI, long_descriptions: str
    ) -> list[SectionCommitted]:
        optional_sections = [
            (idx, s.level, s.title, s.instruction)
            for idx, s in enumerate(self.sections)
            if s.required is False and s.committed_with is None
        ]
        if len(optional_sections) > 0:
            print(
                f"Optional sections for target scope:\n{[title for _, _, title, _ in optional_sections]}\n\n({BLUE}{llm.model}{RESET}) Evaluating optional sections for inclusion..."
            )
            flags = await SectionFlags.from_llm(
                llm=llm,
                goal=self.document.goal,
                preamble=self.scope.preamble,
                optional_sections=optional_sections,
                long_descriptions=long_descriptions,
            )
            included_idxs = set()
            for (idx, level, title, instruction), sf in zip(
                optional_sections, flags.sections
            ):
                if idx != sf.index or title != sf.name:
                    raise ValueError(
                        f"Optional section evaluation returned invalid section: {sf.index} {sf.name}. Expected: {idx} {title}"
                    )
                if sf.flag:
                    print(
                        f"{GREEN}+ {'#' * level} {sf.name}{RESET} ({instruction[:100]} ...)"
                    )
                    included_idxs.add(idx)
                else:
                    print(
                        f"{RED}- {'#' * level} {sf.name}{RESET} ({instruction[:100]} ...)"
                    )

            for idx, section_cfg in enumerate(self.sections):
                if section_cfg.committed_with:
                    for parent_idx, parent_cfg in enumerate(self.sections):
                        if parent_cfg.title == section_cfg.committed_with and (
                            parent_cfg.required or parent_idx in included_idxs
                        ):
                            included_idxs.add(idx)
                            break

            return [
                SectionCommitted.from_section_cfg(cfg)
                for idx, cfg in enumerate(self.sections)
                if (
                    (cfg.required is True and cfg.committed_with is None)
                    or idx in included_idxs
                )
            ]
        else:
            return [SectionCommitted.from_section_cfg(cfg) for cfg in self.sections]


def _autogen_sections(cfg: AutoDocCfg) -> list[SectionCfg]:
    raise NotImplementedError("TODO")


def build_state_filename(scope_roots: list[str], fmt: str, ext: str = ".json") -> str:
    targets = list(
        dict.fromkeys(
            [_get_target_name(code_cfg.node_path) for code_cfg in scope_roots]
        )
    )[:3]
    name = "_".join(targets)
    return f"{name}_{fmt}_iterations{ext}"


def build_annotations_filename(
    scope_roots: list[FullyQualifiedDriverPathCode], fmt: str, ext: str = ".json"
) -> str:
    targets = list(
        dict.fromkeys(
            [_get_codebase_name(code_cfg.node_path) for code_cfg in scope_roots]
        )
    )[:3]
    name = "_".join(targets)
    return f"{name}_{fmt}_annotations{ext}"


class AutoDocInitState(BaseModel):
    llm: LlmCfg
    document: DocumentCfg
    scope: Scope
    sections: list[SectionCommitted]

    def assembly_system_prompt(self) -> str:
        system_prompt_template = """
You are an expert software engineer, technical writer, and copy editor. You specialize in writing documents with the following goal:

{goal}
{preamble_content}

Your job is to assemble a final draft of a document based on a particular structure of sections. You will be given set of detailed content for each section, together covering all of the content we want in the final document.

The content for each section was built up iteratively and these detailed documents were developed independently from each other.

Your job is to combine the information and produce a single high quality, detailed document. Specifically, your primary focus is on consolidating all of the different section content into a single cohesive document.

Your output is the complete document, with all sections combined using Markdown format. Your expected audience is a technical engineer.

I've provided the top-level sections you should use with a description of the kind of content that should be included for each section and the output format expected for that content below. The detailed contents for each section should have all of this content, but you shold focus on making sure the transition between sections is smooth and remove any major redundancies. Use the following top-level structure and output format for the sections of the final document:

{sections}
        """
        sections = ""
        for section in self.sections:
            heading = "#" * section.level
            sections += f"{heading} {section.title}\nContent:{section.instruction}\nFormat:{section.content_structure}\n\n"
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{self.scope.preamble}"
            if self.scope.preamble.strip() != ""
            else ""
        )

        return system_prompt_template.format(
            goal=self.document.goal,
            preamble_content=preamble_content,
            sections=sections,
        )

    def final_copy_editor_system_prompt(self) -> str:
        system_prompt_template = """
You are an expert software engineer, technical writer, and copy editor that specializes in documenting software.

Your job is to provide copy editing for a complete draft of a document using Markdown syntax. The goal of this document is:

{goal}
{preamble_content}

The following section structure should appear in the document. Other subsections are OK, but at least these sections need to be present:

{sections}

This draft was built up iteratively over time.

Your goal is to provide final polish and edits to produce a complete, coherent, and high quality final document. Your job is not to comment or change the content of the document. Focus only on typical copy editing duties:
- Make sure all content is formatted with proper Markdown syntax, but do not enclose any content with triple backticks.
- Remove speculative or hypothetical language.
- Remove any references to this being a draft document, early draft, or iterative draft.
- Keep all technical or conceptual details.
- Ensure the syntax for header and list hierarchies are correct.
- Ensure the syntax for bulleted and numbered lists is correct.
- Make sure transitions between sections and subsections flow smoothly.
- For any MermaidJS diagrams, make sure to not have any parentheses in the MermaidJS content (for example, in the labels for components of the diagram). Parentheses will lead to syntax errors in parsing and rendering the diagram and cannot be allowed. Additionally, make sure labels and names in the diagram are relatively short.

Your output is the full content of the document with editing updates based on your analysis as a copy editor.
        """
        sections = ""
        for section in self.sections:
            heading = "#" * section.level
            sections += f"{heading} {section.title}\n\n"
        preamble_content = (
            f"\nHere is further overall context about the document we are writing:\n\n{self.scope.preamble}"
            if self.scope.preamble.strip() != ""
            else ""
        )

        return system_prompt_template.format(
            goal=self.document.goal,
            preamble_content=preamble_content,
            sections=sections,
        )

    def to_disk(self, json_p: Path) -> None:
        with open(json_p) as f:
            f.write(self.model_dump_json())

    @classmethod
    def from_disk(cls, json_p: Path) -> Self:
        with open(json_p) as f:
            state = json.load(f)
        return cls(**state["cfg"])

    @classmethod
    async def from_cfg(
        cls, cfg: AutoDocCfg, execution_mode: ExecutionMode, page_id: str = ""
    ) -> Self:
        preamble_content = (
            f"\nHere is further context about the document we are writing:\n\n{cfg.scope.preamble}"
            if cfg.scope.preamble.strip() != ""
            else ""
        )
        print(
            f"\n🧙 {CYAN}Whizdoodling{RESET}! to create a document with the following goal:\n{cfg.document.goal}\n{preamble_content}\n"
        )
        print(
            f"Configuration: {cfg.document.config_name} {cfg.document.config_version}"
        )
        print(f"Page ID: {page_id}\n")
        match cfg.document.fmt:
            case DocKind.DEFINED_SECTIONS:
                targets = [
                    [code_cfg.version_id, _get_codebase_name(path=code_cfg.node_path)]
                    for code_cfg in cfg.scope.code
                ]
                match execution_mode:
                    case ExecutionMode.LOCAL:
                        driver_docs = [
                            DriverDocsContent.from_disk(
                                p=_get_path_on_disk(codebase_name=t)
                            )
                            for _, t in targets
                        ]
                    case ExecutionMode.MODAL:
                        driver_docs = [
                            DriverDocsContent.from_db(
                                version_id=code_cfg.version_id,
                                relative_path=code_cfg.node_path,
                            )
                            for code_cfg in cfg.scope.code
                        ]
                    case _:
                        raise ValueError("Invalid execution mode")

                subgraphs = [
                    build_subgraph(dag=dd.dag, start=code_cfg.node_path)
                    for dd, code_cfg in zip(driver_docs, cfg.scope.code)
                ]
                toposorts = [
                    list(TopologicalSorter(sg).static_order()) for sg in subgraphs
                ]
                reverse_topos = [
                    [(p, dd.content[p]) for p in ts]
                    for ts, dd in zip(toposorts, driver_docs)
                ]
                _ = [rt.reverse() for rt in reverse_topos]

                user_prompt = ""
                num_dag_roots = len(reverse_topos)
                ridx = 1
                for rt in reverse_topos:
                    root_p, root_content = rt[0]
                    if root_content.source is None:
                        padding = "\n\n" if ridx == 1 else ""
                        user_prompt += f"{padding}Included root folder {ridx} / {num_dag_roots} (`{root_p}`) description:\n\n{root_content.long_description}"
                        for node_p, node_content in rt[1:]:
                            if node_content.source is None:
                                user_prompt += f"\n\nSubfolder (`{node_p}`) description:\n\n{node_content.long_description}"
                            else:
                                user_prompt += f"\n\nFile (`{node_p}`) description:\n\n{node_content.long_description}"
                    else:
                        user_prompt += f"\n\nFile (`{root_p}`) description:\n\n{root_content.long_description}"
                    ridx += 1
                # TODO: Actually figure out how to handle very large aggregations.
                aggregation_chunks = split_text(
                    text=user_prompt,
                    chunk_size=96_000,
                    chunk_overlap=0,
                )
                llm = ChatOpenAI(
                    model=cfg.llm.tag_model, temperature=0, request_timeout=300
                )
                long_descriptions = aggregation_chunks[0].text
                committed_sections = await cfg.eval_optional_sections(
                    llm=llm, long_descriptions=long_descriptions
                )
                return cls(
                    llm=cfg.llm,
                    document=cfg.document,
                    scope=cfg.scope,
                    sections=committed_sections,
                )
            case DocKind.UNDEFINED:
                sections = _autogen_sections(cfg=cfg)
                return cls(
                    llm=cfg.llm,
                    document=cfg.document,
                    scope=cfg.scope,
                    sections=sections,
                )
            case _:
                raise NotImplementedError("TODO")

    def save_state(
        self,
        revisions: list[dict[str, Any]],
        init_state: dict[str, Any],
        final_doc_revisions: list[str] | None = None,
    ) -> None:
        state_filename = build_state_filename(
            scope_roots=self.scope.code, fmt=self.document.fmt
        )
        init_state = copy.deepcopy(init_state)
        init_state["appended_reverse_topo"] = [
            (p, td.model_dump_json()) for p, td in init_state["appended_reverse_topo"]
        ]
        init_state["init_node_set"] = list(init_state["init_node_set"])
        state = dict()
        state["init_state"] = init_state
        if final_doc_revisions is not None:
            state["final_doc_revisions"] = final_doc_revisions
        state["revisions"] = revisions
        state["cfg"] = self.model_dump()
        with open(state_filename, "w") as f:
            f.write(json.dumps(state))

    def save_annotations(
        self,
        annotations: dict[str, list[Category]],
    ) -> None:
        state_filename = build_annotations_filename(
            scope_roots=self.scope.code, fmt=self.document.fmt
        )
        state = dict()
        state["annotations"] = annotations
        state["cfg"] = self.model_dump()
        with open(state_filename, "w") as f:
            f.write(json.dumps(state))

    def write_final_output_to_markdown(self, output: str) -> None:
        fmt = "document"
        state_filename = build_state_filename(
            scope_roots=self.scope.code,
            fmt=fmt,
            ext=".md",
        )
        with open(state_filename, "w") as f:
            f.write(output)

    def load_state(self) -> list[dict[str, Any]]:
        state_filename = build_state_filename(
            scope_roots=self.scope.code,
            fmt=self.document.fmt,
        )
        with open(state_filename) as f:
            state = json.load(f)

        state["init_state"]["annotations"] = (
            {
                k: [Category(a) for a in v]
                for k, v in state["init_state"]["annotations"].items()
            }
            if self.document.use_tagging
            else None
        )
        state["init_state"]["appended_reverse_topo"] = [
            (p, TechDocsContent.model_validate_json(td))
            for p, td in state["init_state"]["appended_reverse_topo"]
        ]
        state["init_state"]["init_node_set"] = set(state["init_state"]["init_node_set"])
        return state

    def load_annotations(self) -> list[dict[str, Any]]:
        state_filename = build_annotations_filename(
            scope_roots=self.scope.code,
            fmt=self.document.fmt,
        )
        with open(state_filename) as f:
            state = json.load(f)

        annotations = (
            {k: [Category(a) for a in v] for k, v in state["annotations"].items()}
            if self.document.use_tagging
            else None
        )
        cfg = state["cfg"]
        cfg_cls = AutoDocInitState(**cfg)

        return cfg_cls, annotations

    async def _annotate_file(
        self,
        llm: ChatOpenAI,
        node: tuple[str, TechDocsContent],
    ) -> tuple[str, list[Category]]:
        try:
            tech_docs = node[1]
            assert tech_docs.source is not None

            node_list = []

            code_chunks = split_text(
                text=tech_docs.source, chunk_size=64_000, chunk_overlap=0
            )
            user_prompt = f"A single paragraph description of the file to categorize:\n\n{tech_docs.short_paragraph_description}.\n\nThe source code of the file to categorize:\n\n{code_chunks[0].text}"
            async with asyncio.TaskGroup() as tg:
                annotation_task_list = []
                for section in self.sections:
                    annotation_task_list.append(
                        tg.create_task(
                            llm_generate(
                                llm=llm,
                                system_prompt=section.annotation_system_prompt(
                                    goal=self.document.goal,
                                    preamble=self.scope.preamble,
                                ),
                                user_prompt=user_prompt,
                            )
                        )
                    )
            annotations_list = [
                Category.from_str(s=t.result()) for t in annotation_task_list
            ]
            node_list.extend(annotations_list)

        except Exception as e:
            print(f"Error annotating node {node[0]}: {e}")
            return node[0], [Category.Irrelevant for _ in self.sections]

        return node[0], node_list

    async def _annotate_pdf_page(
        self, llm: ChatOpenAI, pdf_text: str, page_idx: int
    ) -> tuple[int, list[Category]]:
        user_prompt = f"The page content of the pdf to categorize:\n\n{pdf_text}"
        annotation_task_list = []
        async with asyncio.TaskGroup() as tg:
            for section in self.sections:
                annotation_task_list.append(
                    tg.create_task(
                        llm_generate(
                            llm=llm,
                            system_prompt=section.pdf_annotation_system_prompt(
                                goal=self.document.goal,
                                preamble=self.scope.preamble,
                            ),
                            user_prompt=user_prompt,
                        )
                    )
                )
        annotations_list = [
            Category.from_str(s=t.result()) for t in annotation_task_list
        ]
        return page_idx, annotations_list

    async def _annotate_nodes(
        self,
        llm: ChatOpenAI,
        topo: list[tuple[str, TechDocsContent]],
        graph: dict[str, set[str]],
        execution_mode: ExecutionMode,
    ) -> dict[str, list[Category]]:
        print(
            f"\n({BLUE}{llm.model}{RESET}) Annotating files for relevance to sections..."
        )
        pidx = 1
        total = len(topo)
        tagged_nodes: dict[str, list[Category]] = dict()
        tagged_pdfs = dict()

        # Annotate files first
        coroutines = []
        for node in topo:
            if node[1].source is not None:
                coroutines.append(self._annotate_file(llm=llm, node=node))
        node_results = await tqdm_asyncio.gather(*coroutines)
        for result in node_results:
            tagged_nodes[result[0]] = result[1]

        # Annotate folders after (since they depend on files)
        for p, tech_docs in topo:
            node_list = []
            if tech_docs.source is None:
                for idx in range(len(self.sections)):
                    if any(
                        tagged_nodes[c][idx] == Category.HighlyRelevant
                        for c in graph[p]
                    ):
                        node_list.append(Category.HighlyRelevant)
                    elif any(
                        tagged_nodes[c][idx] == Category.SomewhatRelevant
                        for c in graph[p]
                    ):
                        node_list.append(Category.SomewhatRelevant)
                    else:
                        node_list.append(Category.Irrelevant)
                tagged_nodes[p] = node_list

        if len(self.scope.pdfs) > 0:
            print(
                f"\n({BLUE}{llm.model}{RESET}) Annotating PDFs for relevance to sections..."
            )
            pidx = 1
            total = len(self.scope.pdfs)
            pdf_paths = _get_pdf_paths(
                [pdf_cfg.pdf_name for pdf_cfg in self.scope.pdfs],
                execution_mode=execution_mode,
            )
            for pdf in pdf_paths:
                coroutines = []
                tagged_pdfs[pdf] = dict()
                print(f"[{pidx} / {total}] Annotating `{GREEN}{pdf}{RESET}`...")
                with fitz.open(pdf) as doc:
                    for idx, _ in enumerate(doc):
                        md_text = pymupdf4llm.to_markdown(
                            pdf, pages=[idx], show_progress=False
                        )
                        coroutines.append(
                            self._annotate_pdf_page(
                                llm=llm, pdf_text=md_text, page_idx=idx
                            )
                        )
                pdf_results = await tqdm_asyncio.gather(*coroutines)
                for result in pdf_results:
                    tagged_pdfs[pdf][result[0]] = result[1]

        return tagged_nodes, tagged_pdfs

    async def _initialize_sections(
        self,
        llm: ChatOpenAI,
        reverse_topos_from_start: list[list[str]],
        driver_docs: list[DriverDocsContent],
        annotations: dict[str, list[Category]],
        pdf_annotations: dict,
        execution_mode: ExecutionMode,
    ) -> tuple[set[str], list[dict[str, str]]]:
        if self.scope.pdfs and any(
            s.section_creation_method == SectionCreationMethod.ONLY_PDFS
            for s in self.sections
        ):
            pdf_paths = _get_pdf_paths(
                [pdf_cfg.pdf_name for pdf_cfg in self.scope.pdfs],
                execution_mode=execution_mode,
            )
            api_key = os.environ.get("GEMINI_API_KEY")
            client = genai.Client(api_key=api_key)
            gemini_model_id = "gemini-2.0-flash"
            pdf_handles = []
            for pdf in pdf_paths:
                pdf_handles.append(
                    client.files.upload(file=pdf, config={"display_name": pdf.name})
                )
        else:
            pdf_handles = None

        init_sections_dict = {}
        init_node_set = set()
        # Content from code.
        # Build context from root + first level children only.
        # TODO: the way sections are created could use a refactor - right now, each method is done in sequence
        # We should consider having a function for each method that can be awaited simulatenously
        if any(
            s.section_creation_method == SectionCreationMethod.SEQUENTIAL_EDIT
            for s in self.sections
        ):
            raw_user_prompt = ""
            num_roots = len(reverse_topos_from_start)
            ridx = 1
            for dag_topo, docs in zip(reverse_topos_from_start, driver_docs):
                root_p, root_content = dag_topo[0]
                init_node_set.add(root_p)
                if root_content.source is None:
                    padding = "\n\n" if ridx == 1 else ""
                    raw_user_prompt += f"{padding}Included root folder {ridx} / {num_roots} (`{root_p}`) description:\n\n{root_content.long_description}"
                    children = list(docs.dag[root_p])
                    for child in children:
                        init_node_set.add(child)
                        child_content = docs.content[child]
                        if child_content.source is None:
                            raw_user_prompt += f"\n\nSubfolder (`{child}`) description:\n\n{child_content.long_description}"
                        else:
                            raw_user_prompt += f"\n\nFile (`{child}`) description:\n\n{child_content.long_description}"
                else:
                    raw_user_prompt += f"\n\nFile (`{root_p}`) description:\n\n{root_content.long_description}"
            # TODO: Actually figure out how to handle very large aggregations.
            aggregation_chunks = split_text(
                text=raw_user_prompt,
                chunk_size=96_000,
                chunk_overlap=0,
            )
            user_prompt = aggregation_chunks[0].text

            # TODO: This de-mixing and then re-mixing between lists and dicts is ugly.
            # TODO: Do this better, assume need to separate async part out this way for now.

            # Use `idx` to preserve order info and guard against non-unique section titles.
            prompt_pairs_dict_code = {
                idx: (
                    s.init_draft_system_prompt_code(
                        goal=self.document.goal, preamble=self.scope.preamble
                    ),
                    user_prompt,
                )
                for idx, s in enumerate(self.sections)
                if s.section_creation_method == SectionCreationMethod.SEQUENTIAL_EDIT
            }
            async with asyncio.TaskGroup() as tg:
                init_section_tasks_code = dict()
                for k, (system_prompt, user_prompt) in prompt_pairs_dict_code.items():
                    init_section_tasks_code[k] = tg.create_task(
                        llm_generate(
                            llm=llm,
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                        )
                    )
            init_sections_dict = {
                k: v.result() for k, v in init_section_tasks_code.items()
            }

        if any(
            s.section_creation_method == SectionCreationMethod.SCATTER_GATHER
            for s in self.sections
        ):
            scatter_gather_indices = []
            scatter_gather_coroutines = []
            for idx, s in enumerate(self.sections):
                if s.section_creation_method == SectionCreationMethod.SCATTER_GATHER:
                    print(f"creating {s.title} via scatter-gather...")
                    scatter_gather_indices.append(idx)
                    scatter_gather_coroutines.append(
                        s.create_section_scatter_gather(
                            goal=self.document.goal,
                            preamble=self.scope.preamble,
                            reverse_topos=reverse_topos_from_start,
                            pdf_paths=_get_pdf_paths(
                                [pdf_cfg.pdf_name for pdf_cfg in self.scope.pdfs],
                                execution_mode=execution_mode,
                            ),
                            tagged_nodes=annotations,
                            pdf_tagged_nodes=pdf_annotations,
                            tag_idx=idx,
                            section_name=s.title,
                        )
                    )
            scatter_gather_results = await asyncio.gather(*scatter_gather_coroutines)
            for idx, result in zip(scatter_gather_indices, scatter_gather_results):
                init_sections_dict[idx] = result

        if any(
            s.section_creation_method == SectionCreationMethod.CODE_EXAMPLE
            for s in self.sections
        ):
            code_example_single_pass_indices = []
            code_example_single_pass_coroutines = []
            for idx, s in enumerate(self.sections):
                if s.section_creation_method == SectionCreationMethod.CODE_EXAMPLE:
                    print(f"creating {s.title} via code example single pass...")
                    code_example_single_pass_indices.append(idx)
                    code_example_single_pass_coroutines.append(
                        s.code_example_few_shot_generator(
                            document_goal=self.document.goal,
                            document_preamble=self.scope.preamble,
                            reverse_topos=reverse_topos_from_start,
                            tagged_nodes=annotations,
                            tag_idx=idx,
                        )
                    )
            code_example_single_pass_results = await asyncio.gather(
                *code_example_single_pass_coroutines
            )
            for idx, result in zip(
                code_example_single_pass_indices, code_example_single_pass_results
            ):
                init_sections_dict[idx] = result

        # Content from PDFs.
        prompt_dict_pdf = {
            idx: s.init_draft_system_prompt_pdf(
                goal=self.document.goal, preamble=self.scope.preamble
            )
            for idx, s in enumerate(self.sections)
            if s.section_creation_method == SectionCreationMethod.ONLY_PDFS
        }
        for k, prompt in prompt_dict_pdf.items():
            contents = [prompt]
            contents.extend(pdf_handles)
            init_sections_dict[k] = client.models.generate_content(
                model=gemini_model_id,
                contents=contents,
            ).text

        max_idx = max(init_sections_dict.keys())
        init_sections = []
        for idx in range(max_idx + 1):
            section_info = {
                "order_idx": idx,
                "title": self.sections[idx].title,
                "content": init_sections_dict[idx],
            }
            init_sections.append(section_info)

        assert len(self.sections) == len(init_sections)

        return init_node_set, init_sections

    async def _update_sections(
        self,
        llm: ChatOpenAI,
        node_name: str,
        previous_state: list[dict[str, str]],
        tech_docs: TechDocsContent,
        annotations: list[Category] | None,
    ) -> dict[str, str]:
        assert len(previous_state) == len(self.sections)
        common_update_prompt = f"\n\nNow update this document, as appropriate, given the following detailed content from (`{node_name}`):\n\n"
        common_description_prompt = (
            f"DESCRIPTION of `{node_name}`:\n\n{tech_docs.long_description}\n\n"
        )
        prompt_pairs = []
        if tech_docs.source is not None and tech_docs.source.strip() == "":
            return previous_state

        # TODO: Just do this better here and elsewhere with similar processing:
        # TODO: wastefully creating prompts when annotations say some or irrelevant, and
        # TODO: awkward logic to keep same-sized list processing for every section even though
        # TODO: now some are explicitly not to be processed. This all started because it
        # TODO: wasn't clear what key to use for sections (non-unique titles), etc. Should
        # TODO: just make `SectionCommitted` hashable and good to go.
        for idx in range(len(previous_state)):
            assert self.sections[idx].title == previous_state[idx]["title"]
            user_prompt = f"Current state of the {self.sections[idx].title} section:\n\n{previous_state[idx]['content']}"
            user_prompt += common_update_prompt
            user_prompt += common_description_prompt
            if tech_docs.source is not None:
                system_prompt = self.sections[idx].update_from_file_system_prompt(
                    goal=self.document.goal,
                    preamble=self.scope.preamble,
                )
                # TODO: Actually figure out how to handle very large files.
                code_chunks = split_text(
                    text=tech_docs.source,
                    chunk_size=64_000,
                    chunk_overlap=0,
                )
                user_prompt += (
                    f"SOURCE CODE for `{node_name}`:\n\n{code_chunks[0].text}\n\n"
                )
                if llm.model == "o1-mini":
                    user_prompt = f"{system_prompt}\n\n{user_prompt}"
            else:
                system_prompt = self.sections[idx].update_from_folder_system_prompt(
                    goal=self.document.goal, preamble=self.scope.preamble
                )

            prompt_pairs.append((system_prompt, user_prompt))

        async with asyncio.TaskGroup() as tg:
            section_tasks = []
            for idx, (system_prompt, user_prompt) in enumerate(prompt_pairs):
                if annotations is not None:
                    not_relevant = annotations[idx] == Category.Irrelevant
                else:
                    not_relevant = False
                if (
                    not_relevant
                    or self.sections[idx].section_creation_method
                    != SectionCreationMethod.SEQUENTIAL_EDIT
                ):
                    section_tasks.append(None)
                else:
                    section_tasks.append(
                        tg.create_task(
                            llm_generate(
                                llm=llm,
                                system_prompt=system_prompt,
                                user_prompt=user_prompt,
                            )
                        )
                    )

        new_state = []
        for idx, task in enumerate(section_tasks):
            if task is None:
                new_state.append(previous_state[idx])
            else:
                new_state.append(
                    {
                        "order_idx": previous_state[idx]["order_idx"],
                        "title": previous_state[idx]["title"],
                        "content": task.result(),
                    }
                )

        return new_state

    async def _update_sections_with_pdf(
        self,
        llm: ChatOpenAI,
        previous_state: list[dict[str, str]],
        pdf_path: str,
        pdf_annotations: list[Category] | None,
    ) -> dict[str, str]:
        # NOTE: Currently doing the whole PDF in one function, can save state between pages if needed at a later point.

        assert len(previous_state) == len(self.sections)
        common_update_prompt = f"\n\nNow update this document, as appropriate, given the following content from a page of the pdf (`{pdf_path}`):\n\n"

        temp_results = [
            previous_state[idx]["content"] for idx in range(len(previous_state))
        ]
        with fitz.open(pdf_path) as doc:
            for pg_idx, _ in enumerate(doc):
                prompt_pairs = []
                pdf_md = pymupdf4llm.to_markdown(
                    pdf_path, pages=[pg_idx], show_progress=False
                )
                for idx in range(len(previous_state)):
                    user_prompt = f"Current state of the {self.sections[idx].title} section:\n\n{temp_results[idx]}"
                    user_prompt += common_update_prompt
                    user_prompt += f"PDF PAGE CONTENT for `{pdf_path}`:\n\n{pdf_md}"
                    system_prompt = self.sections[idx].update_from_pdf_system_prompt(
                        goal=self.document.goal,
                        preamble=self.scope.preamble,
                    )
                    prompt_pairs.append((system_prompt, user_prompt))
                async with asyncio.TaskGroup() as tg:
                    section_tasks = []
                    for idx, (system_prompt, user_prompt) in enumerate(prompt_pairs):
                        if pdf_annotations is not None:
                            relevant = (
                                pdf_annotations[pg_idx][idx] == Category.HighlyRelevant
                            )  # Only doing highly relevant for pdf pages
                        else:
                            relevant = True
                        if (
                            not relevant
                            or self.sections[idx].section_creation_method
                            != SectionCreationMethod.SEQUENTIAL_EDIT
                        ):
                            section_tasks.append(None)
                        else:
                            section_tasks.append(
                                tg.create_task(
                                    llm_generate(
                                        llm=llm,
                                        system_prompt=system_prompt,
                                        user_prompt=user_prompt,
                                    )
                                )
                            )
                new_temp_results = []
                for idx, task in enumerate(section_tasks):
                    if task is None:
                        new_temp_results.append(temp_results[idx])
                    else:
                        new_temp_results.append(task.result())
                temp_results = new_temp_results

        new_state = []
        for idx, result in enumerate(temp_results):
            new_state.append(
                {
                    "order_idx": previous_state[idx]["order_idx"],
                    "title": previous_state[idx]["title"],
                    "content": result,
                }
            )
        return new_state

    async def _final_section_format(
        self, llm: ChatOpenAI, previous_state: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        assert len(previous_state) == len(self.sections)

        prompt_pairs = []
        for idx in range(len(previous_state)):
            assert self.sections[idx].title == previous_state[idx]["title"]
            user_prompt = f"Detailed {previous_state[idx]['title']} section content:\n\n{previous_state[idx]['content']}"
            system_prompt = self.sections[idx].final_output_format(
                goal=self.document.goal,
                preamble=self.scope.preamble,
            )
            prompt_pairs.append((system_prompt, user_prompt))

        async with asyncio.TaskGroup() as tg:
            section_tasks = []
            for system_prompt, user_prompt in prompt_pairs:
                section_tasks.append(
                    tg.create_task(
                        llm_generate(
                            llm=llm,
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                        )
                    )
                )

        new_state = []
        for idx, task in enumerate(section_tasks):
            new_state.append(
                {
                    "order_idx": previous_state[idx]["order_idx"],
                    "title": previous_state[idx]["title"],
                    "content": task.result(),
                }
            )

        return new_state

    async def generate(
        self,
        execution_mode: ExecutionMode,
        resume: bool = False,
        page_id: str | None = None,
    ) -> str:
        llm_tagging = ChatOpenAI(
            model=self.llm.tag_model, temperature=0, request_timeout=300
        )
        llm_section_init = ChatOpenAI(
            model=self.llm.section_init_model, temperature=0, request_timeout=300
        )
        llm_section_update = ChatOpenAI(
            model=self.llm.section_update_model, temperature=0, request_timeout=300
        )
        llm_section_format = ChatOpenAI(
            model=self.llm.section_format_model, temperature=0, request_timeout=500
        )
        llm_assembly = ChatOpenAI(
            model=self.llm.assembly_model, temperature=0, request_timeout=900
        )
        llm_copy_editor = ChatOpenAI(
            model=self.llm.copy_editor_model, temperature=0, request_timeout=900
        )

        # Download PDFS if needed
        if execution_mode == ExecutionMode.MODAL:
            pdf_ids = [pdf_cfg.version_id for pdf_cfg in self.scope.pdfs]
            for pdf_id in pdf_ids:
                _download_pdf_from_s3(version_id=pdf_id)

        # Handle resume
        if resume:
            state = self.load_state()
            revisions = state["revisions"]
            init_state = state["init_state"]
            annotations = init_state["annotations"]
            init_node_set = init_state["init_node_set"]
            appended_reverse_topo = init_state["appended_reverse_topo"]
            section_state = revisions[-1]
            pidx = section_state["_index"]
            preamble_content = (
                f"\nHere is further context about the document we are writing:\n\n{self.scope.preamble}"
                if self.scope.preamble.strip() != ""
                else ""
            )
            print(
                f"\n🧙 {CYAN}Whizdoodling{RESET}! to create a document with the following goal:\n{self.document.goal}\n{preamble_content}\n"
            )
        else:
            # Create path traversal state.
            targets = [
                [code_cfg.version_id, _get_codebase_name(path=code_cfg.node_path)]
                for code_cfg in self.scope.code
            ]
            match execution_mode:
                case ExecutionMode.LOCAL:
                    driver_docs = [
                        DriverDocsContent.from_disk(
                            p=_get_path_on_disk(codebase_name=t)
                        )
                        for [_, t] in targets
                    ]
                case ExecutionMode.MODAL:
                    driver_docs = [
                        DriverDocsContent.from_db(
                            version_id=code_cfg.version_id,
                            relative_path=code_cfg.node_path,
                        )
                        for code_cfg in self.scope.code
                    ]
                case _:
                    raise ValueError("Invalid execution mode")
            subgraphs = [
                build_subgraph(dag=dd.dag, start=code_cfg.node_path)
                for dd, code_cfg in zip(driver_docs, self.scope.code)
            ]
            toposorts = [list(TopologicalSorter(sg).static_order()) for sg in subgraphs]
            topos = [
                [(p, dd.content[p]) for p in ts]
                for ts, dd in zip(toposorts, driver_docs)
            ]
            reverse_topos = [
                [(p, dd.content[p]) for p in ts]
                for ts, dd in zip(toposorts, driver_docs)
            ]
            _ = [rt.reverse() for rt in reverse_topos]
            appended_topo = [tup for t in topos for tup in t]
            appended_reverse_topo = [tup for rt in reverse_topos for tup in rt]
            joined_graph = {k: v for dd in driver_docs for k, v in dd.dag.items()}

            if execution_mode == ExecutionMode.MODAL:
                await update_autodocs_status(
                    page_id=page_id,
                    status_kind=AutoDocStatusMessageKind.EVALUATING_SOURCES,
                    content="Evaluating sources for relevance...",
                )

            # Annotate nodes with tags, if applicable.
            annotations, pdf_annotations = (
                await self._annotate_nodes(
                    llm=llm_tagging,
                    topo=appended_topo,
                    graph=joined_graph,
                    execution_mode=execution_mode,
                )
                if self.document.use_tagging
                else (None, None)
            )
            # self.save_annotations(annotations=annotations)
            if execution_mode == ExecutionMode.MODAL:
                await update_autodocs_status(
                    page_id=page_id,
                    status_kind=AutoDocStatusMessageKind.GENERATING_SECTION_DRAFTS,
                    content="Generating initial section drafts...",
                )

            pidx = 1
            section_state = dict()
            revisions = []

            # Initial draft creation
            print(
                f"\n({BLUE}{self.llm.section_init_model}{RESET}) Building initial section drafts for target scope in `{self.scope.code}`..."
            )
            init_node_set, sections_init = await self._initialize_sections(
                llm=llm_section_init,
                reverse_topos_from_start=reverse_topos,
                driver_docs=driver_docs,
                annotations=annotations,
                pdf_annotations=pdf_annotations,
                execution_mode=execution_mode,
            )
            section_state["sections"] = sections_init
            section_state["_index"] = pidx
            revisions.append(section_state)

            init_state = {
                "annotations": annotations,
                "appended_reverse_topo": appended_reverse_topo,
                "init_node_set": init_node_set,
            }
            self.save_state(revisions=revisions, init_state=init_state)

        # Exhaustive updates
        if any(
            s.section_creation_method == SectionCreationMethod.SEQUENTIAL_EDIT
            for s in self.sections
        ):
            total = len(appended_reverse_topo)
            print(
                f"\n({BLUE}{self.llm.section_update_model}{RESET}) Iteratively improving the initial state of the documents..."
            )
            for p, tech_docs in appended_reverse_topo[pidx - 1 :]:
                if p in init_node_set and tech_docs.source is None:
                    print(
                        f"[{pidx} / {total}] Already assessed folder `{GREEN}{p}{RESET}` in building initial sections..."
                    )
                    pidx += 1
                    continue
                print(
                    f"[{pidx} / {total}] Updating sections with content from `{GREEN}{p}{RESET}`..."
                )
                new_section_state = dict()
                section_update = await self._update_sections(
                    llm=llm_section_update,
                    node_name=p,
                    previous_state=section_state["sections"],
                    tech_docs=tech_docs,
                    annotations=annotations[p] if annotations is not None else None,
                )
                pidx += 1

                new_section_state["sections"] = section_update
                new_section_state["_index"] = pidx
                revisions.append(new_section_state)
                self.save_state(revisions=revisions, init_state=init_state)
                section_state = new_section_state

            if len(self.scope.pdfs) > 0:
                pdf_paths = _get_pdf_paths(
                    [pdf_cfg.pdf_name for pdf_cfg in self.scope.pdfs],
                    execution_mode=execution_mode,
                )
                for pdf_path in pdf_paths[pidx - total - 1 :]:
                    print(f"Updating sections with content from {pdf_path}...")
                    new_section_state = dict()
                    section_update = await self._update_sections_with_pdf(
                        llm=llm_section_update,
                        previous_state=section_state["sections"],
                        pdf_path=pdf_path,
                        pdf_annotations=pdf_annotations[pdf_path],
                    )
                    pidx += 1
                    new_section_state["sections"] = section_update
                    new_section_state["_index"] = pidx
                    revisions.append(new_section_state)
                    self.save_state(revisions=revisions, init_state=init_state)
                    section_state = new_section_state

        if execution_mode == ExecutionMode.MODAL:
            await update_autodocs_status(
                page_id=page_id,
                status_kind=AutoDocStatusMessageKind.OPTIMIZING_SECTION_STRUCTURE,
                content="Optimizing content structure for each section...",
            )
        # Final output format enforcement
        print(
            f"\n({BLUE}{self.llm.section_format_model}{RESET}) Final section output structure pass..."
        )
        new_section_state = dict()
        final_section_update = await self._final_section_format(
            llm=llm_section_format, previous_state=section_state["sections"]
        )
        pidx += 1
        new_section_state["sections"] = final_section_update
        new_section_state["_index"] = pidx
        revisions.append(new_section_state)
        self.save_state(revisions=revisions, init_state=init_state)
        section_state = new_section_state
        if execution_mode == ExecutionMode.MODAL:
            await update_autodocs_status(
                page_id=page_id,
                status_kind=AutoDocStatusMessageKind.ASSEMBLING_FINAL_DOCUMENT,
                content="Assembling all sections into a single document...",
            )

        # Final document assembly
        final_doc_revisions = []
        print(
            f"\n({BLUE}{self.llm.assembly_model}{RESET}) Full document assembly pass..."
        )
        assembly_user_prompt = "Document draft content:"
        for section in section_state["sections"]:
            assembly_user_prompt += f"\n\nDRAFT content for section {section['title']}:\n\n{section['content']}"
        full_document = await llm_assembly.generate_response(
            system_prompt=self.assembly_system_prompt(),
            user_prompt=assembly_user_prompt,
        )
        final_doc_revisions.append(full_document)
        self.save_state(
            revisions=revisions,
            init_state=init_state,
            final_doc_revisions=final_doc_revisions,
        )

        if execution_mode == ExecutionMode.MODAL:
            await update_autodocs_status(
                page_id=page_id,
                status_kind=AutoDocStatusMessageKind.COPY_EDITING,
                content="Copy editing and finalizing document...",
            )
        # Final copy editor pass
        print(
            f"\n({BLUE}{self.llm.copy_editor_model}{RESET}) Final copy editor pass..."
        )
        copy_editor_user_prompt = f"Document draft:\n\n{full_document}"
        final_document = await llm_copy_editor.generate_response(
            system_prompt=self.final_copy_editor_system_prompt(),
            user_prompt=copy_editor_user_prompt,
        )
        final_document += "\n\nMade with ❤️ by [Driver](https://www.driver.ai/)"
        final_doc_revisions.append(final_document)
        self.save_state(
            revisions=revisions,
            init_state=init_state,
            final_doc_revisions=final_doc_revisions,
        )

        # Write final output to a separate file.
        self.write_final_output_to_markdown(output=final_doc_revisions[-1])

        return final_doc_revisions[-1]


async def main(args: argparse.Namespace) -> None:
    if args.validate:
        validated_cfg = AutoDocCfg.from_file(toml_file=args.validate)
        if not args.quiet:
            print(validated_cfg.model_dump_json(indent=2))
        print(f"\n\nFile `{args.validate}` is valid and ready for processing!")
    elif args.execute:
        init_state = await AutoDocInitState.from_cfg(
            cfg=AutoDocCfg.from_file(toml_file=args.execute),
            execution_mode=ExecutionMode.LOCAL,
        )
        doc = await init_state.generate(execution_mode=ExecutionMode.LOCAL)
        if not args.quiet:
            console = Console()
            console.print(Markdown(doc))
    elif args.resume:
        cfg = AutoDocCfg.from_file(toml_file=args.resume)
        state_filename = build_state_filename(
            scope_roots=cfg.scope.code, fmt=cfg.document.fmt
        )
        state = AutoDocInitState.from_disk(json_p=state_filename)
        doc = await state.generate(resume=True, execution_mode=ExecutionMode.LOCAL)
        if not args.quiet:
            console = Console()
            console.print(Markdown(doc))
    else:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mutex_group = parser.add_mutually_exclusive_group(required=True)
    mutex_group.add_argument(
        "-v",
        "--validate",
        help="validate the given configuration file",
        metavar="TOML FILE",
        type=str,
    )
    mutex_group.add_argument(
        "-e",
        "--execute",
        help="execute content generation with the given configuration file",
        metavar="TOML FILE",
        type=str,
    )
    mutex_group.add_argument(
        "-r",
        "--resume",
        help="resume execution",
        metavar="TOML FILE",
        type=str,
    )
    parser.add_argument(
        "-q",
        "--quiet",
        help="do not render final output",
        action="store_true",
    )

    args = parser.parse_args()
    asyncio.run(main(args))
