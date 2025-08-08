import asyncio
import os
import uuid

import modal
from common import app
from database.models_v2_enums import ContentKind
from utils.synthesis.deep_context import DeepContextDoc, DeepContextDocKind
from utils.synthesis.deep_context_prompts import (
    ARCHITECTURE_OVERVIEW_INTENT,
    LLM_ONBOARDING_INTENT,
)

deep_context_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/shared_pkg", copy=True
    )
    .pip_install(
        [
            "openai==1.99.1",
            "pydantic>=2.8.2",
            "/shared_pkg",
        ]
    )
    .add_local_python_source(
        "inspection",
        "modal_funcs",
        "main",
        "onboarding",
        "shared",
        "tasks",
        "utils",
        "common",
        "database",
        copy=True,
        ignore=lambda p: False,  # recent modal version only copy .py by default, but we have text files, for example, that we want
    )
)


@app.function(
    image=deep_context_image,
    secrets=[
        modal.Secret.from_name("db"),
    ],
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging", "prod"]
    else None,
    memory=4096,
    timeout=3600 * 12,
    region="us-east",
    max_containers=5,
    cpu=1.0,
)
async def deep_context_docs(
    version_id: uuid.UUID,
) -> list[DeepContextDoc]:
    from database.models_v2_enums import AutoDocConfigKind, VersionStatus
    from utils.db import get_version_by_id

    version = await get_version_by_id(version_id)
    root_node_id = version.root_node.id

    run_autodoc = modal.Function.from_name(app_name="autodocs", name="run_autodoc")

    print("Creating deep context docs for version:", version_id)
    deep_context_doc_tasks = [
        run_autodoc.remote.aio(
            page_node_id=str(root_node_id),
            config_kind=AutoDocConfigKind.FROM_DOCUMENT_GOAL,
            document_goal=ARCHITECTURE_OVERVIEW_INTENT,
            user_context="SHORT",
            content_kind=ContentKind.DEEP_CONTEXT_ARCHITECTURE,
        ),
        run_autodoc.remote.aio(
            page_node_id=str(root_node_id),
            config_kind=AutoDocConfigKind.FROM_DOCUMENT_GOAL,
            document_goal=LLM_ONBOARDING_INTENT,
            user_context="SHORT",
            content_kind=ContentKind.DEEP_CONTEXT_LLM_ONBOARDING,
        ),
    ]
    completed_docs = []

    for (
        content_kind,
        title,
        user_context_str,
        sources,
        config_content,
        doc_content,
    ) in await asyncio.gather(*deep_context_doc_tasks):
        completed_docs.append(
            DeepContextDoc(
                doc_kind=DeepContextDocKind.from_content_kind(
                    content_kind=content_kind
                ),
                name=title,
                user_context={"desired_length": user_context_str}
                if user_context_str
                else None,
                sources=sources,
                config_content=config_content,
                doc_content=doc_content,
            )
        )

    status_func = modal.Function.from_name(
        app_name="inspector-v2", name="set_codebase_status_in_container"
    )
    await status_func.remote.aio(
        version_id=version_id,
        status=VersionStatus.GENERATION_COMPLETE,
    )

    return completed_docs
