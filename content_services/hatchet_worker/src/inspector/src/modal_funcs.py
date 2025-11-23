import os
import uuid

from shared.inspector.inspection.files import comprehend_file_top_down
from shared.inspector.utils.dag import LiteNode


def make_tech_doc(
    node: LiteNode,
    codebase_name: str,
    source_code: str,
    version_id: str,
) -> tuple[bool, dict, LiteNode]:
    import os

    import boto3
    from shared.inspector.utils.io import download_symbol_table_from_s3_with_cache
    from shared.inspector.utils.models import ChatOpenAI

    print(f"Processing tech docs ({node})")

    raise_hard_errors = False
    llm = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0,
        request_timeout=FILE_TECH_DOC_LLM_TIMEOUT,
    )

    s3_client = boto3.client("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    print("Pre-bucket name fetch")
    bucket_name = os.environ.get("BUCKET_NAME")
    if bucket_name is None:
        print("================================")
        print(node.root_rel_path)
        print(os.environ)
        print("================================")
        raise ValueError("BUCKET_NAME environment variable is not set")

    full_symbol_table = download_symbol_table_from_s3_with_cache(
        s3_client=s3_client,
        bucket_name=bucket_name,
        version_id=version_id,
    )
    reified_symbols = full_symbol_table.get(node.root_rel_path, None)

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
    return {"success": file_docs_successful, "file_doc": file_doc, "node": node}


def make_symbol_docs(
    node: LiteNode,
    source_code: str,
    file_description_paragraph: str,
    symbol_count_limit: int | None = None,
) -> list[dict[str, any]]:
    from shared.inspector.inspection.symbols import document_symbols_in_file

    print(f"Processing symbol docs ({node})")
    symbols = document_symbols_in_file(
        file_node=node,
        source_code=source_code,
        file_description_paragraph=file_description_paragraph,
        symbol_count_limit=symbol_count_limit,
    )
    print(f"Symbol docs created for {node}")
    return {"symbols": symbols}


def make_folder_tech_doc(
    codebase_name: str,
    node: LiteNode,
    child_nodes_to_docs: dict[LiteNode, dict],
    previous_content: dict[str, str] | None = None,
) -> dict[str, any]:
    from shared.inspector.inspection.folders import comprehend_folder_top_down
    from shared.inspector.utils.models import ChatOpenAI

    llm = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0,
        request_timeout=FOLDER_TECH_DOC_LLM_TIMEOUT,
    )

    print(f"Processing folder tech docs for ({node.root_rel_path.name})")
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


def make_toplevel_tech_docs(
    codebase_name: str, nodes_to_docs: dict[LiteNode, dict]
) -> dict[str, any]:
    from shared.inspector.inspection.toplevel import comprehend_codebase_top_down
    from shared.inspector.utils.models import ChatOpenAI

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


def make_codebase_tags(
    codebase_name: str,
    nodes_to_docs: dict[LiteNode, dict],
    content_kinds: set,
) -> dict[str, any]:
    from shared.inspector.inspection.toplevel import tag_codebase
    from shared.inspector.utils.models import ChatOpenAI

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
    from shared.inspector.utils.export_utils import (
        replace_driver_compatible_links_with_markdown_links,
    )
    from sqlalchemy.orm import selectinload
    from sqlmodel import Session, select

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
        make_archive(f"{version_id}_tech_docs", "zip", Path(temp_dir))

        s3_resource = boto3.resource(
            "s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL")
        )
        s3_dest = f"{primary_asset_id}/{version_id}/{version_id}_tech_docs.zip"
        s3_bucket = s3_resource.Bucket(org_id_hash)
        if install_id is not None:
            s3_bucket.upload_file(
                Path(f"{version_id}_tech_docs.zip"),
                s3_dest,
                ExtraArgs={"Metadata": {"install_id": install_id}},
            )
        else:
            s3_bucket.upload_file(
                Path(f"{version_id}_tech_docs.zip"),
                s3_dest,
            )
        print(f"Uploaded tech docs zip to S3: {s3_dest}")
        if auto_commit_docs:
            if install_id is not None:
                print("PRing exported docs")
                from shared.inspector.onboarding.push_bot import push_docs

                push_docs(version_id)
            else:
                # TODO: better handling of install_id rather than attaching to S3 metadata
                print("Unable to PR - install id is not available")
        else:
            print("PR disabled for this codebase.")
        # Delete zip after upload
        os.remove(f"{version_id}_tech_docs.zip")


CHUNK_SIZE = 64_000
CHUNK_OVERLAP = 3_000
COMPRESSION_LOOP_MAX_ITR = 10
MAX_NUM_CHUNKS_FILE = 10
FILE_TECH_DOC_LLM_TIMEOUT = 500
FOLDER_TECH_DOC_LLM_TIMEOUT = 500
TOP_LEVEL_DOC_LLM_TIMEOUT = 500
