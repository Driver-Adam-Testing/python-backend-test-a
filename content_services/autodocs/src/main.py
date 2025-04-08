import os
import uuid

import modal
from autodocs_prototype import (
    AutoDocCfg,
    AutoDocInitState,
    ExecutionMode,
    FullyQualifiedDriverPathCode,
    FullyQualifiedDriverPathPdf,
    Scope,
    update_autodocs_status,
)

image = inspection_image = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir(local_path="../../driver_db", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/shared_pkg")
    .pip_install(
        [
            "boto3",
            "requests",
            "openai>=1.40.2",
            "pydantic>=2.8.2",
            "tiktoken",
            "/shared_pkg",
            "pymupdf4llm",
            "google-genai",
        ]
    )
)

app = modal.App("autodocs")


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("open-ai"),
    ],
    mounts=[
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
        modal.Mount.from_local_file(
            "src/adi_driver_v4.toml", "/autodocs_configs/adi_driver_page.toml"
        ),
    ],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "dev-shane"
    else None,
    memory="2048",
    timeout=3600 * 8,
    region="us-east",
    concurrency_limit=5,
)
async def run_adi_driver(
    page_node_id: uuid.UUID,
) -> None:
    from database.db import get_session
    from database.models_v1 import DerivedContent, DocumentSource
    from database.models_v2 import Node, Version
    from database.models_v2_enums import (
        AutoDocStatusMessageKind,
        ContentKind,
        PrimaryAssetKind,
        VersionStatus,
    )
    from sqlalchemy.orm import selectinload
    from sqlmodel import select

    # Get document sources given page id
    with get_session() as session, session.begin():
        document_sources = session.exec(
            select(DocumentSource)
            .where(DocumentSource.page_node_id == page_node_id)
            .options(
                selectinload(DocumentSource.source_node)
                .selectinload(Node.version)
                .selectinload(Version.primary_asset)
            )
        ).all()

        scope = Scope(
            preamble="",
            code=[],
            pdfs=[],
        )

        for source in document_sources:
            if (
                source.source_node.version.primary_asset.kind
                == PrimaryAssetKind.CODEBASE
            ):
                code_cfg = FullyQualifiedDriverPathCode(
                    version_id=str(source.source_node.version_id),
                    node_path=source.source_node.relative_path.rstrip("/"),
                )
                scope.code.append(code_cfg)
            elif source.source_node.version.primary_asset.kind == PrimaryAssetKind.FILE:
                pdf_cfg = FullyQualifiedDriverPathPdf(
                    version_id=str(source.source_node.version_id),
                    pdf_name=source.source_node.version.primary_asset.display_name,
                )
                scope.pdfs.append(pdf_cfg)

    config = AutoDocCfg.from_file("/autodocs_configs/adi_driver_page.toml")
    config.scope = scope
    print(config.scope)

    init_state = await AutoDocInitState.from_cfg(
        cfg=config,
        execution_mode=ExecutionMode.MODAL,
    )
    doc = await init_state.generate(
        execution_mode=ExecutionMode.MODAL, page_id=str(page_node_id)
    )
    await update_autodocs_status(
        page_id=str(page_node_id),
        status_kind=AutoDocStatusMessageKind.GENERATION_COMPLETE,
        content=doc,
    )
    with get_session() as session, session.begin():
        derived_content = session.exec(
            select(DerivedContent).where(
                DerivedContent.node_id == page_node_id,
                DerivedContent.content_kind == ContentKind.application_note,
            )
        ).first()
        if not derived_content:
            print("No existing derived content found for this page node.")
            return
        else:
            derived_content.content = doc
        node = session.exec(
            select(Node)
            .where(Node.id == page_node_id)
            .options(selectinload(Node.version))
        ).one()

        node.version.status = VersionStatus.GENERATION_COMPLETE
        session.add(node.version)

    print("Updated derived content for page node:", page_node_id)


@app.local_entrypoint()
def main(
    page_node_id: str,
) -> None:
    run_adi_driver.remote(page_node_id=page_node_id)
