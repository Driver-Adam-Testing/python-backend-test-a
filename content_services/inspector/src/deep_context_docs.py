# TODO !!!!!!!!!!!!! NOTE THIS FILE IS NOT CURRENTLY PICKED UP BY MODAL !!!!!!!!!!!!
# COPIED deep_context_docs function to main.py for testing purposes
import asyncio
import os
import uuid

import modal
from common import app

inspection_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/shared_pkg", copy=True
    )
    .pip_install(
        [
            "boto3",
            "requests",
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
            "chardet",
        ]
    )
    .add_local_python_source(
        "inspection",
        "modal_funcs",
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
    image=inspection_image,
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
) -> None:
    from database.models_v2_enums import AutoDocConfigKind, VersionStatus
    from utils.db import get_version_by_id

    version = await get_version_by_id(version_id)
    root_node_id = version.root_node.id

    run_autodoc = modal.Function.from_name(app_name="autodocs", name="run_autodocs")

    print("Creating deep context docs for version:", version_id)
    deep_context_doc_tasks = [
        run_autodoc.remote.aio(
            page_node_id=str(root_node_id),
            config_kind=AutoDocConfigKind.FROM_DOCUMENT_GOAL,
            document_goal="Architecture document",
            user_context="SHORT",
            is_page=False,
            deep_context_kind="architecture",  # TODO: enum
        ),
        run_autodoc.remote.aio(
            page_node_id=str(root_node_id),
            config_kind=AutoDocConfigKind.FROM_DOCUMENT_GOAL,
            document_goal="LLM overview",
            user_context="SHORT",
            is_page=False,
            deep_context_kind="overview",  # TODO: enum
        ),
    ]
    await asyncio.gather(*deep_context_doc_tasks)

    status_func = modal.Function.from_name(
        app_name="inspector-v2", name="set_codebase_status_in_container"
    )
    await status_func.remote.aio(
        version_id=version_id,
        status=VersionStatus.GENERATION_COMPLETE,
    )
