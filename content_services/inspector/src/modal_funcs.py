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
            "httpx==0.28.1",
            "pyjwt==2.10.1",
            "requests==2.32.3",
            "openai==1.99.1",
            "pydantic>=2.8.2",
            "tiktoken",
            "/shared_pkg",
            "tree-sitter==0.24.0",
            "tree-sitter-c==0.23.4",
            "tree-sitter-cpp==0.23.2",
            "tree-sitter-java==0.23.5",
            "tree-sitter-python==0.23.6",
            "tree-sitter-c-sharp==0.23.1",
            "tree-sitter-typescript==0.23.2",
            "aiolimiter==1.2.1",
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
        ignore=lambda p: False,
    )
)


@app.function(
    max_containers=72,
    timeout=180 * 60,
    secrets=[
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
    image=image,
)
def make_tech_doc(
    node: LiteNode,
    source_code: str,
    codebase_name: str,
    sym_table_s3_key: str | None,
) -> tuple[bool, dict, LiteNode]:
    from utils.models import ChatOpenAI

    print(f"Processing tech docs ({node})")
    raise_hard_errors = False
    llm = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0,
        request_timeout=FILE_TECH_DOC_LLM_TIMEOUT,
    )

    reified_symbols = None
    if sym_table_s3_key is not None:
        import pickle

        import boto3

        if sym_table_s3_key is not None:
            s3 = boto3.client("s3")
            bucket_name = os.environ["BUCKET_NAME"]
            obj = s3.get_object(Bucket=bucket_name, Key=sym_table_s3_key)
            reified_symbols = pickle.loads(obj["Body"].read())

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


function_cfg = {
    "secrets": [
        modal.Secret.from_name("open-ai"),
    ],
    "image": image,
}


@app.function(max_containers=72, timeout=120 * 60, **function_cfg)
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
    codebase_name: str,
    node: LiteNode,
    child_nodes_to_docs: dict[LiteNode, dict],
    previous_content: dict[str, str] | None = None,
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
        previous_content=previous_content,
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


@app.function(max_containers=1, timeout=60 * 60, **function_cfg)
def make_codebase_tags(
    codebase_name: str,
    nodes_to_docs: dict[LiteNode, dict],
    content_kinds: set,
) -> dict[str, any]:
    from inspection.toplevel import tag_codebase
    from utils.models import ChatOpenAI

    llm = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0,
        request_timeout=TOP_LEVEL_DOC_LLM_TIMEOUT,
    )

    print(f"Processing tags for `{codebase_name}`")
    tags = tag_codebase(
        llm=llm,
        docs=nodes_to_docs,
        content_kinds=content_kinds,
    )
    print(f"Processed tags for `{codebase_name}`")
    return tags


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging"]
    else modal.Proxy.from_name("my-proxy", environment_name="prod"),
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
    from database.models import DerivedContent, Node, Version
    from database.models_enums import ContentKind, NodeKind
    from sqlalchemy.orm import selectinload
    from sqlmodel import Session, select
    from utils.export_utils import (
        replace_driver_compatible_links_with_markdown_links,
    )

    with Session(engine) as session:
        long_desc_query = (
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

        short_desc_query = (
            select(
                Node,
                DerivedContent,
            )
            .join(DerivedContent)
            .where(
                Node.version_id == version_id,
                DerivedContent.content_kind == ContentKind.SHORT_SENTENCE_DESCRIPTION,
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

        long_desc_result = session.exec(long_desc_query)
        long_desc_rows = long_desc_result.all()

        short_desc_result = session.exec(short_desc_query)
        short_desc_rows = short_desc_result.all()

        node_to_short_desc = {
            node.id: derived_content for node, derived_content in short_desc_rows
        }

        node_path_to_kind = {
            Path(node.relative_path): node.kind for node, _ in long_desc_rows
        }
    with (
        tempfile.TemporaryDirectory() as temp_dir,
    ):
        for node, long_desc_dc in long_desc_rows:
            node_path = Path(node.relative_path)
            if node.kind == NodeKind.CODEBASE_FILE:
                link_destination_path = node_path.with_suffix(node_path.suffix + ".md")
                file_path = Path(temp_dir) / link_destination_path
            elif node.kind == NodeKind.CODEBASE_DIRECTORY:
                if node_path.name == ".github":
                    # NOTE: we special case .github here, because Github priotizes displaying
                    # the README.md file from the .github folder over the README.md file in the root of the repo
                    # See: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
                    link_destination_path = node_path / "README_.md"
                    file_path = Path(temp_dir) / link_destination_path
                else:
                    link_destination_path = node_path / "README.md"
                    file_path = Path(temp_dir) / link_destination_path
                # doc_file_path = node_path.with_suffix(".driver.md")

            short_desc_dc = node_to_short_desc.get(node.id)

            # Combine short and long descriptions as we do in the frontend display
            content = ""
            if short_desc_dc and short_desc_dc.content:
                content += short_desc_dc.content + "\n\n"
            content += long_desc_dc.content

            content = replace_driver_compatible_links_with_markdown_links(
                content,
                Path(*link_destination_path.parts[1:]),
                node_path.suffix,
                node_path_to_kind,
            )
            file_path.parent.mkdir(parents=True, exist_ok=True)
            comment = (
                "<!--------------------------------------------------------------------------------->\n"
                "<!-- IMPORTANT: This file is auto-generated by Driver (https://driver.ai). -------->\n"
                "<!-- Manual edits may be overwritten on future commits. --------------------------->\n"
                "<!--------------------------------------------------------------------------------->\n\n"
            )
            end_comment = "\n---\nMade with ❤️ by [Driver](https://www.driver.ai/)"
            content = comment + content + end_comment
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
    # my-proxy defines the static IP that we share today with "on the beach". Not only does OTB whitelist this IP we also
    # whitelist this IP with ScaleGrid for our DB.
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging"]
    else modal.Proxy.from_name("my-proxy", environment_name="prod"),
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
