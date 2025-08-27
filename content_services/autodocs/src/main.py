import os
import uuid
from math import ceil
from typing import Any

import modal
from auto_toml import AutoToml
from autodoc_log import AutoDocLog, write_autodoc_log
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
from common import app, wait_for_guard_duty_tag
from database.models_v2_enums import ContentKind

image = inspection_image = (
    modal.Image.debian_slim(python_version="3.12")
    # NOTE: order matters here - anything needed for the build must be added with
    # copy=True before other actions, all other files must be added after all other
    # actions
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/shared_pkg", copy=True
    )
    .add_local_dir(
        local_path="../auto_toml/src", remote_path="/auto_toml_src", copy=True
    )
    .pip_install(
        [
            "boto3",
            "requests",
            "openai==1.99.1",
            "pydantic>=2.8.2",
            "tiktoken",
            "/shared_pkg",
            "pymupdf4llm==0.0.17",
            "google-genai",
            "aiolimiter",
        ]
    )
    .env({"PYTHONPATH": "/auto_toml_src"})
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
        "autodocs_prototype",
        "common",
        "database",
        "shared",
        "utils",
        "autodoc_log",
        copy=True,
        ignore=lambda p: False,
    )
)

# app = modal.App("autodocs")


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("open-ai"),
    ],
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging", "prod"]
    else None,
    memory=2048,
    timeout=3600 * 8,
    region="us-east",
    max_containers=5,
)
async def run_autodoc(
    page_node_id: uuid.UUID,  # TODO: naming here
    config_kind: Any,  # TODO: the actual type is a deferred import here, not sure how to resolve?
    document_goal: str | None = None,
    user_context: str | None = None,
    content_kind: ContentKind | None = None,
) -> None:
    import hashlib

    import boto3
    from database.db import get_session
    from database.models_v1 import DerivedContent, DocumentSource
    from database.models_v2 import Node, UserCache, Version, VersionCreator
    from database.models_v2_enums import (
        AutoDocConfigKind,
        AutoDocStatusMessageKind,
        ContentKind,
        PrimaryAssetKind,
        VersionStatus,
    )
    from sqlalchemy.orm import selectinload
    from sqlmodel import delete, select

    is_page = content_kind == ContentKind.application_note or content_kind is None

    toml_content = ""

    if config_kind == AutoDocConfigKind.FROM_DOCUMENT_GOAL and not document_goal:
        raise ValueError(
            "document_goal is required when config_kind is FROM_DOCUMENT_GOAL"
        )

    try:
        # Get document sources given page id
        if is_page:
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

                org_id = None
                for source in document_sources:
                    if not org_id:
                        org_id = (
                            source.source_node.version.primary_asset.organization_id
                        )
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
        else:
            scope = Scope(
                preamble="",
                code=[],
                pdfs=[],
            )
            with get_session() as session, session.begin():
                node = session.get(Node, page_node_id)
                code_cfg = FullyQualifiedDriverPathCode(
                    version_id=str(node.version_id),
                    node_path=node.relative_path.rstrip("/"),
                )
                scope.code.append(code_cfg)

        match config_kind:
            case AutoDocConfigKind.ADI_DRIVER:
                config = AutoDocCfg.from_file("/autodocs_configs/adi_driver_page.toml")
            case AutoDocConfigKind.ARCHITECTURE:
                config = AutoDocCfg.from_file(
                    "/autodocs_configs/architecture_modal.toml"
                )
            case AutoDocConfigKind.CUSTOM:
                if org_id:
                    bucket = os.environ.get("DROPZONE_BUCKET_NAME")
                    hashed_org_id = hashlib.sha256(org_id.encode()).hexdigest()[:63]
                    key = f"assets/{hashed_org_id}/{page_node_id}/custom_config.toml"

                    s3 = boto3.client("s3")
                    # download the file from S3
                    if wait_for_guard_duty_tag(bucket=bucket, key=key):
                        print(
                            f"Downloading custom config from bucket {bucket} with key {key}."
                        )
                        s3.download_file(
                            bucket,
                            key,
                            "/autodocs_configs/custom_config.toml",
                        )
                    else:
                        raise ValueError(
                            f"GuardDuty tag not found for bucket {bucket} and key {key}. "
                        )
                    config = AutoDocCfg.from_file(
                        "/autodocs_configs/custom_config.toml"
                    )
                    with open("/autodocs_configs/custom_config.toml") as f:
                        toml_content = f.read()

            case AutoDocConfigKind.FROM_DOCUMENT_GOAL:
                toml_file = "config.toml"
                if is_page:
                    auto_toml = AutoToml.from_page_id(
                        page_node_id, enable_auto_scaling=True
                    )
                else:
                    auto_toml = AutoToml.from_root_node_id(
                        root_node_id=page_node_id, enable_auto_scaling=True
                    )
                toml_content = await auto_toml.generate(
                    document_goal=document_goal,
                    user_context=user_context if user_context else "",
                )
                with open(toml_file, "w") as f:
                    f.write(toml_content)
                config = AutoDocCfg.from_file(toml_file=toml_file)
            case _:
                raise ValueError(f"Unsupported config kind: {config_kind}")

        scope.preamble = config.scope.preamble
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

        sections = []
        section_refs = []
        for (
            section_title,
            source_list,
        ) in init_state.section_sources.items():
            section = f"{section_title}\n\n" + "\n".join(source_list)
            sections.append(section)
            section_refs.append((section_title, source_list))
        source_string = "\n\n".join(sections)

        # dataset to return
        name = None
        user_context_str = user_context
        sources = section_refs
        config_content = toml_content
        doc_content = doc

        if is_page:
            with get_session() as session, session.begin():
                derived_content = session.exec(
                    select(DerivedContent).where(
                        DerivedContent.node_id == page_node_id,
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
                    .options(
                        selectinload(Node.version).selectinload(Version.primary_asset)
                    )
                ).one()

                node.version.status = VersionStatus.GENERATION_COMPLETE
                session.add(node.version)

                user_cache = session.exec(
                    select(UserCache)
                    .join(VersionCreator, UserCache.id == VersionCreator.user_id)
                    .where(VersionCreator.version_id == node.version_id)
                ).first()

                env = os.environ.get("MODAL_ENVIRONMENT")

                name = derived_content.content_name if derived_content else "UNKNOWN"
                if env in ["prod", "staging"]:
                    print("Writing AutoDoc log to Notion")

                    log = AutoDocLog(
                        title=name,
                        user_email=user_cache.email if user_cache else "UNKNOWN",
                        organization_id=node.version.primary_asset.organization_id
                        if node
                        else "UNKNOWN",
                        sources=source_string,
                        toml_content=toml_content,
                        autodoc_content=doc,
                        user_context=user_context,
                        env=env,
                        page_id=str(page_node_id),
                        config_kind=str(config_kind),
                    )
                    write_autodoc_log.spawn(log)

            print("Updated derived content for page node:", page_node_id)
        else:
            with get_session() as session, session.begin():
                node = session.get(Node, page_node_id)
                dc_delete_query = delete(DerivedContent).where(
                    DerivedContent.node_id == page_node_id,
                    DerivedContent.content_kind == content_kind,
                )
                session.exec(dc_delete_query)

                derived_content = DerivedContent(
                    node_id=page_node_id,
                    relative_path=node.relative_path,
                    content_kind=content_kind,  # TODO: doc kind as input
                    content=doc,
                    misc_metadata=None,
                )
                session.add(derived_content)

        return (
            content_kind,
            name,
            user_context_str,
            sources,
            config_content,
            doc_content,
        )

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
        raise e

        raise


@app.local_entrypoint()
def main(
    page_node_id: str,  # page_node_id - if this is a codebase deep context doc, you want to save as such, use the root node id!
) -> None:
    from database.models_v2_enums import AutoDocConfigKind, ContentKind

    document_goal = """
Your task is to build deep context documents for codebases for downstream LLM agent consumption. That is, you will pre-compile information on specific topics ahead of time for codebases so that downstream LLM agent chat/interactions can be greatly improved. A common issue for large codebases an LLM was not trained on, is that LLM agents equipped with only basic file discovery tools or even indexing that supports semantic search cannot effectively or timely navigate to the sets of places in the codebase critical for input tasks. To resolve this, we can pre-compute information about these codebases ahead of time and provide this in the form documents. You will write an exhaustive and information dense document in this manner. Through integrations such as an MCP service, this information can be fetched and referred to trivially quickly when a downstream LLM agent needs to help a user in real time.

Since you are building dense documents for an entire codebase, it is important to be judicious with what you focus on and how much content you produce for each topic. Look for all opportunities to be brief while making sure importance concepts are covered. Only devote a significant amount of content to topics critically important for the codebase and for a downstream agent to be aware of up front. Focus on text output such as paragraphs, lists, and tables. Do not use diagrams and code blocks unless critically important or useful.

Your focus in particular is to build an Architecture Overview deep context document. The goal is to provide a document that explains the architecture of the codebase effectively but densely, so that given a broad task (e.g., consider a 10 million line codebase), an LLM agent can refer to this document first and then have a good grasp of the overall architecture. An architecture document can take many forms depending on the context, kind, and size of the codebase, but you should focus on the best dense representation for an LLM to quickly reason appropriately about the architecture of a codebase. Focus more on the conceptual level and be exhaustive -- key components and emergent structure rather than low-level mechanical information such as the directory structure. Major architectural components, functionality provided by the codebase as a whole, and how they fit together are prime topics.

Write an architecture document for this codebase for the purpose articulated above.

In your document, do not allude to the fact that this is being written for an LLM. Just write the content of the document per the instructions.
"""
    user_context = "SHORT"
    # Set content_kind to LLM_ONBOARDING or ARCHITECTURE to save it as a deep context doc, if you're using a page id, switch this to ContentKind.application_note
    content_kind = ContentKind.DEEP_CONTEXT_ARCHITECTURE

    ################ LLM Onboarding example ################
    #     document_goal = """
    # Your task is to build deep context documents for codebases for downstream LLM agent consumption. That is, you will pre-compile information on specific topics ahead of time for codebases so that downstream LLM agent chat/interactions can be greatly improved. A common issue for large codebases an LLM was not trained on, is that LLM agents equipped with only basic file discovery tools or even indexing that supports semantic search cannot effectively or timely navigate to the sets of places in the codebase critical for input tasks. To resolve this, we can pre-compute information about these codebases ahead of time and provide this in the form documents. You will write an exhaustive and information dense document in this manner. Through integrations such as an MCP service, this information can be fetched and referred to trivially quickly when a downstream LLM agent needs to help a user in real time.

    # Since you are building dense documents for an entire codebase, it is important to be judicious with what you focus on and how much content you produce for each topic. Look for all opportunities to be brief while making sure importance concepts are covered. Only devote a significant amount of content to topics critically important for the codebase and for a downstream agent to be aware of up front. Focus on text output such as paragraphs, lists, and tables. Do not use diagrams and code blocks unless critically important or useful.

    # Your focus in particular is to build an Onboarding Guide deep context document. The idea is to provide a document that best "onboards" an LLM agent to the codebase, enabling the LLM coding agent to immediately know what to do/where to go next in its workflows to accomplish user's tasks (e.g., as input in an IDE chat experience). Density and exhaustiveness are critical but fundamentally a tradeoff.

    # Consider an LLM coding agent given a broad task in the context of a very large codebase (e.g., consider a 10 million line codebase). We want to build a deep context LLM onboarding guide that the LLM agent can refer to first and then be very efficient in subsequent steps because this document provided all of the context needed

    # Focus on ways of best describing the contents of the codebase itself and how/where to navigate to for more detailed information. Useful topics include capabilities, critical components and where to find their implementations, important components to consider together or in cross-reference and "tips and tricks" for an agent to navigate the codebase. Keep content focused on the codebase and how to navigate it rather than anything else about what an LLM agent should do in its workflow. The goal is to provide all of the information necessary about the codebase so that an LLM agent is equipped to make these decisions on its own.

    # Write an LLM onboarding guide for this codebase for the purpose articulated above.

    # In your document, do not allude to the fact that this is being written for an LLM. Just write the content of the document per the instructions.
    # """
    #     user_context = "SHORT"
    #     # Set content_kind to LLM_ONBOARDING or ARCHITECTURE to save it as a deep context doc, if you're using a page id, switch this to ContentKind.application_note
    #     content_kind = ContentKind.DEEP_CONTEXT_LLM_ONBOARDING

    run_autodoc.remote(
        page_node_id=page_node_id,
        config_kind=AutoDocConfigKind.FROM_DOCUMENT_GOAL,
        document_goal=document_goal,
        user_context=user_context,
        content_kind=content_kind,
    )


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging", "prod"]
    else None,
    memory="2048",
    timeout=3600 * 8,
    region="us-east",
    max_containers=5,
)
async def run_autodoc_cli(toml_content: str, page_node_id: str) -> None:
    from database.db import get_session
    from database.models_v1 import DocumentSource
    from database.models_v2 import Node, Version
    from database.models_v2_enums import (
        PrimaryAssetKind,
    )
    from sqlalchemy.orm import selectinload
    from sqlmodel import select

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

        org_id = None
        for source in document_sources:
            if not org_id:
                org_id = source.source_node.version.primary_asset.organization_id
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

        config_file = "config_file.toml"
        with open(config_file, "w") as f:
            f.write(toml_content)

        config = AutoDocCfg.from_file(toml_file=config_file)
        scope.preamble = config.scope.preamble
        config.scope = scope

        init_state = await AutoDocInitState.from_cfg(
            cfg=config, execution_mode=ExecutionMode.MODAL, page_id=page_node_id
        )
        doc = await init_state.generate(
            execution_mode=ExecutionMode.MODAL, page_id=str(page_node_id)
        )
        return doc
