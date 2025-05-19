import os
import uuid
from math import ceil
from typing import Any

import modal
from autodocs_prototype import (
    AutoDocCfg,
    AutoDocInitState,
    ExecutionMode,
    FullyQualifiedDriverPathCode,
    FullyQualifiedDriverPathPdf,
    Scope,
    get_autodoc_elapsed_time,
    update_autodocs_status,
)

image = inspection_image = (
    modal.Image.debian_slim(python_version="3.12")
    # NOTE: order matters here - anything needed for the build must be added with
    # copy=True before other actions, all other files must be added after all other
    # actions
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/shared_pkg", copy=True
    )
    .pip_install(
        [
            "boto3",
            "requests",
            "openai>=1.40.2",
            "pydantic>=2.8.2",
            "tiktoken",
            "/shared_pkg",
            "pymupdf4llm==0.0.17",
            "google-genai",
            "aiolimiter",
        ]
    )
    .add_local_file(
        "src/configs/adi_driver_readme.toml",
        "/autodocs_configs/adi_driver_page.toml",
        copy=True,
    )  # These shouldn't require the copy, but seems to be conflicting with the Proxy
    .add_local_file(
        "src/configs/architecture_modal.toml",
        "/autodocs_configs/architecture_modal.toml",
        copy=True,
    )
    .add_local_python_source(
        "autodocs_prototype", "database", "shared", "utils", copy=True
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
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "prod"]
    else None,
    memory="2048",
    timeout=3600 * 8,
    region="us-east",
    max_containers=5,
)
async def run_autodoc(
    page_node_id: uuid.UUID,
    config_kind: Any,  # noqa: ANN401 #TODO: the actual type is a deferred import here, not sure how to resolve?
) -> None:
    from database.db import get_session
    from database.models_v1 import DerivedContent, DocumentSource
    from database.models_v2 import Node, Version
    from database.models_v2_enums import (
        AutoDocConfigKind,
        AutoDocStatusMessageKind,
        ContentKind,
        PrimaryAssetKind,
        VersionStatus,
    )
    from sqlalchemy.orm import selectinload
    from sqlmodel import select

    try:
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
                elif (
                    source.source_node.version.primary_asset.kind
                    == PrimaryAssetKind.FILE
                ):
                    pdf_cfg = FullyQualifiedDriverPathPdf(
                        version_id=str(source.source_node.version_id),
                        pdf_name=source.source_node.version.primary_asset.display_name,
                    )
                    scope.pdfs.append(pdf_cfg)

        match config_kind:
            case AutoDocConfigKind.ADI_DRIVER:
                config = AutoDocCfg.from_file("/autodocs_configs/adi_driver_page.toml")
            case AutoDocConfigKind.ARCHITECTURE:
                config = AutoDocCfg.from_file(
                    "/autodocs_configs/architecture_modal.toml"
                )
            case _:
                raise ValueError(f"Unsupported config kind: {config_kind}")
        config.scope = scope
        print(config.scope)

        init_state = await AutoDocInitState.from_cfg(
            cfg=config, execution_mode=ExecutionMode.MODAL, page_id=page_node_id
        )
        doc = await init_state.generate(
            execution_mode=ExecutionMode.MODAL, page_id=str(page_node_id)
        )
        elapsed_time_s = await get_autodoc_elapsed_time(
            page_id=str(page_node_id),
        )
        elapsed_time_min = ceil(elapsed_time_s / 60)
        if elapsed_time_min == 1:
            doc += f" in {elapsed_time_min} minute"
        else:
            doc += f" in {elapsed_time_min} minutes"
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
    except Exception as e:
        print("Error:", e)
        await update_autodocs_status(
            page_id=str(page_node_id),
            status_kind=AutoDocStatusMessageKind.GENERATION_ERROR,
            content="An error as has occurred during generation.",
        )
        with get_session() as session, session.begin():
            node = session.get(Node, page_node_id)
            node.version.status = VersionStatus.GENERATION_ERROR
            session.add(node.version)


@app.local_entrypoint()
def main(
    page_node_id: str,
) -> None:
    from database.models_v2_enums import AutoDocConfigKind

    run_autodoc.remote(
        page_node_id=page_node_id, config_kind=AutoDocConfigKind.ADI_DRIVER
    )
