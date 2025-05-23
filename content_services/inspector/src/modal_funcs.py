import os
import uuid

import modal
from common import app
from inspection.files import comprehend_file_top_down
from utils.dag import LiteNode

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/shared_pkg", copy=True
    )
    .add_local_file(
        local_path="uctags-2024.10.02-linux-x86_64/bin/ctags",
        remote_path="/ctags",
        copy=True,
    )
    .pip_install(
        [
            "boto3==1.37.22",
            "cryptography==44.0.2",
            "gitignore-parser==0.1.11",
            "httpx==0.28.1",
            "pyjwt==2.10.1",
            "requests==2.32.3",
            "openai>=1.40.2",
            "pydantic>=2.8.2",
            "tiktoken",
            "/shared_pkg",
            "tree-sitter==0.24.0",
            "tree-sitter-c==0.23.4",
        ]
    )  # TODO lock versions down
    .add_local_python_source(
        "common",
        "database",
        "inspection",
        "main",
        "onboarding",
        "shared",
        "tasks",
        "utils",
        copy=True,
    )
)

function_cfg = {"secrets": [modal.Secret.from_name("open-ai")], "image": image}


@app.function(
    max_containers=72,
    timeout=120 * 60,
    **function_cfg,
)
def make_tech_doc(
    node: LiteNode,
    source_code: str,
    codebase_name: str,
    reified_symbols: dict | None,  # TODO: what is the correct type for reified_symbols?
) -> tuple[bool, dict, LiteNode]:
    from utils.models import ChatOpenAI

    print(f"Processing tech docs ({node})")
    raise_hard_errors = False
    llm = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0,
        request_timeout=FILE_TECH_DOC_LLM_TIMEOUT,
    )

    file_docs_successful, file_doc = comprehend_file_top_down(
        llm=llm,
        node=node,
        source_code=source_code,
        codebase_name=codebase_name,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        compression_loop_max_itr=COMPRESSION_LOOP_MAX_ITR,
        max_num_chunks=MAX_NUM_CHUNKS_FILE,
        reified_symbols=reified_symbols,
        raise_hard_errors=raise_hard_errors,
    )
    print(f"Tech docs created for ({node})")
    return file_docs_successful, file_doc, node


@app.function(max_containers=72, timeout=60 * 60, **function_cfg)
def make_symbol_docs(
    node: LiteNode,
    source_code: str,
    file_description_paragraph: str,
    symbol_count_limit: int | None = None,
) -> list[dict[str, any]]:
    from inspection.symbols import document_symbols_in_file

    print(f"Processing symbol docs ({node})")
    symbols = document_symbols_in_file(
        file_node=node,
        source_code=source_code,
        file_description_paragraph=file_description_paragraph,
        symbol_count_limit=symbol_count_limit,
    )
    print(f"Symbol docs created for {node}")
    return symbols


@app.function(max_containers=60, timeout=30 * 60, **function_cfg)
def make_folder_tech_doc(
    codebase_name: str, node: LiteNode, child_nodes_to_docs: dict[LiteNode, dict]
) -> dict[str, any]:
    from inspection.folders import comprehend_folder_top_down
    from utils.models import ChatOpenAI

    llm = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0,
        request_timeout=FOLDER_TECH_DOC_LLM_TIMEOUT,
    )

    print(f"Processing folder tech docs for ({node})")
    folder_docs = comprehend_folder_top_down(
        llm=llm,
        codebase_name=codebase_name,
        node=node,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        max_workers=1,
        child_nodes_to_docs=child_nodes_to_docs,
        compression_loop_max_itr=COMPRESSION_LOOP_MAX_ITR,
    )
    print(f"Folder tech docs created for ({node})")
    return folder_docs


@app.function(max_containers=3, timeout=60 * 60, **function_cfg)
def make_toplevel_tech_docs(
    codebase_name: str, nodes_to_docs: dict[LiteNode, dict]
) -> dict[str, any]:
    from inspection.toplevel import comprehend_codebase_top_down
    from utils.models import ChatOpenAI

    llm = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0,
        request_timeout=TOP_LEVEL_DOC_LLM_TIMEOUT,
    )

    print(f"Processing top-level docs for `{codebase_name}`")
    top_level_docs = comprehend_codebase_top_down(
        llm=llm,
        docs=nodes_to_docs,
        codebase_name=codebase_name,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        max_workers=20,
        include_exploratory_generation=False,
        compression_loop_max_itr=COMPRESSION_LOOP_MAX_ITR,
    )
    print(f"Processed top-level docs for `{codebase_name}`")
    return top_level_docs


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "prod"]
    else None,
    memory=2048,
    timeout=3600 * 8,
    region="us-east",
    max_containers=5,
    cpu=1.0,
)
def export_tech_docs_to_zip(
    version_id: uuid.UUID,
    install_id: str | None = None,
) -> None:
    import hashlib
    import tempfile
    from pathlib import Path
    from shutil import make_archive

    import boto3
    from database.db import engine
    from database.models_v1 import DerivedContent
    from database.models_v2 import Node, Version
    from database.models_v2_enums import ContentKind, NodeKind
    from sqlalchemy.orm import selectinload
    from sqlmodel import Session, select
    from utils.export_utils import (
        replace_driver_compatible_links_with_markdown_links,
    )

    with Session(engine) as session:
        nodes_query = (
            select(
                Node,
                DerivedContent,
                # Node.relative_path, DerivedContent.content, Node.kind, Node.depth
            )
            .join(DerivedContent)
            .where(
                Node.version_id == version_id,
                DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION,
            )
        )
        version_query = (
            select(Version)
            .where(Version.id == version_id)
            .options(
                selectinload(Version.primary_asset),
            )
        )
        version_result = session.exec(version_query)
        version_row = version_result.one()
        primary_asset_id = version_row.primary_asset_id
        auto_commit_docs = version_row.primary_asset.codebase_settings_auto_commit_docs
        org_id = version_row.primary_asset.organization_id
        org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
        result = session.exec(nodes_query)
        node_rows = result.all()
    with (
        tempfile.TemporaryDirectory() as temp_dir,
    ):
        for node, derived_content in node_rows:
            if node.depth != 0:
                node_path = Path(node.relative_path)
                if node.kind == NodeKind.CODEBASE_FILE:
                    doc_file_path = node_path.with_suffix(
                        node_path.suffix + ".driver.md"
                    )
                elif node.kind == NodeKind.CODEBASE_DIRECTORY:
                    doc_file_path = node_path.with_suffix(".driver.md")
                content = replace_driver_compatible_links_with_markdown_links(
                    derived_content.content, Path(*doc_file_path.parts[1:])
                )
                file_path = Path(temp_dir) / doc_file_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
        make_archive("tech_docs", "zip", Path(temp_dir))

        s3_resource = boto3.resource(
            "s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL")
        )
        s3_dest = f"{primary_asset_id}/{version_id}/{version_id}_tech_docs.zip"
        s3_bucket = s3_resource.Bucket(org_id_hash)
        if install_id is not None:
            s3_bucket.upload_file(
                Path("tech_docs.zip"),
                s3_dest,
                ExtraArgs={"Metadata": {"install_id": install_id}},
            )
        else:
            s3_bucket.upload_file(
                Path("tech_docs.zip"),
                s3_dest,
            )
        print(f"Uploaded tech docs zip to S3: {s3_dest}")
        if auto_commit_docs:
            if install_id is not None:
                print("PRing exported docs")
                push_tech_docs.remote(version_id)
            else:
                # TODO: better handling of install_id rather than attaching to S3 metadata
                print("Unable to PR - install id is not available")
        else:
            print("PR disabled for this codebase.")


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("db"),
        modal.Secret.from_name("github-app"),
    ],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "prod"]
    else None,
    timeout=60 * 60,
    region="us-east",
    max_containers=5,
)
async def push_tech_docs(version_id: str) -> None:
    """Push tech docs to s3"""
    from onboarding.push_bot import push_docs

    await push_docs(version_id)


CHUNK_SIZE = 64_000
CHUNK_OVERLAP = 3_000
COMPRESSION_LOOP_MAX_ITR = 10
MAX_NUM_CHUNKS_FILE = 10
FILE_TECH_DOC_LLM_TIMEOUT = 500
FOLDER_TECH_DOC_LLM_TIMEOUT = 500
TOP_LEVEL_DOC_LLM_TIMEOUT = 500
