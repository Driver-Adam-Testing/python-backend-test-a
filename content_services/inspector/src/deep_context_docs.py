import asyncio
import os
import uuid

import modal
from common import app
from database.models_enums import ContentKind
from utils.dag import FlatTopoFileDiffDag
from utils.synthesis.deep_context import DeepContextDoc

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
            "aiolimiter==1.2.1",
            "tiktoken",
            "httpx==0.28.1",
            "pyjwt==2.10.1",
            "requests==2.32.3",
            "pygit2==1.18.1",
            "cryptography==44.0.2",
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
        modal.Secret.from_name("github-app"),
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
    # my-proxy defines the static IP that we share today with "on the beach". Not only does OTB whitelist this IP we also
    # whitelist this IP with ScaleGrid for our DB.
    proxy=(
        modal.Proxy.from_name("my-proxy")
        if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging"]
        else modal.Proxy.from_name("my-proxy", environment_name="prod")
    ),
    timeout=60 * 60,
    region="us-east",
    max_containers=5,
)
async def make_changelog(
    version_id: str,
    install_id: str,
) -> None:
    from database.db import async_engine
    from database.models import DerivedContent
    from inspection.changelog import create_changelog
    from sqlmodel import delete
    from sqlmodel.ext.asyncio.session import AsyncSession
    from utils.db import get_version_by_id

    print(f"Making changelog for version {version_id}")
    content_kind = ContentKind.DEEP_CONTEXT_CHANGELOG
    version = await get_version_by_id(version_id)
    root_node_id = version.root_node.id
    root_node_relative_path = version.root_node.relative_path
    repo_id = version.primary_asset.repository_id
    if repo_id is None:
        print("No repo_id found, skipping changelog generation.")
        return content_kind, "", "", [], "", ""
    print(f"Creating changelog for version {version_id}")
    changelog = await create_changelog(version_id=version_id, install_id=install_id)
    print("Changelog content:", changelog["overall_changelog"])

    # TODO: IO okay here?
    # TODO: delete old changelog for the node before saving
    async with AsyncSession(async_engine) as session:
        dc_delete_query = delete(DerivedContent).where(
            DerivedContent.node_id == root_node_id,
            DerivedContent.content_kind == content_kind,
        )
        await session.exec(dc_delete_query)
        await session.commit()

        derived_content = DerivedContent(
            node_id=root_node_id,
            relative_path=root_node_relative_path,
            content_kind=content_kind,
            content=changelog["overall_changelog"],
            misc_metadata=changelog["monthly_changelogs"],
        )
        session.add(derived_content)
        await session.commit()

    name = "Changelog"
    user_context_str = ""
    sources = []
    config_content = ""
    doc_content = changelog["overall_changelog"]
    return (
        content_kind,
        name,
        user_context_str,
        sources,
        config_content,
        doc_content,
    )


@app.function(
    image=deep_context_image,
    secrets=[
        modal.Secret.from_name("db"),
    ],
    proxy=(
        modal.Proxy.from_name("my-proxy")
        if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging"]
        else modal.Proxy.from_name("my-proxy", environment_name="prod")
    ),
    memory=4096,
    timeout=3600 * 12,
    region="us-east",
    max_containers=5,
    cpu=1.0,
)
async def deep_context_docs(
    old_version_id: uuid.UUID | None,
    old_version_content: list[DeepContextDoc] | None,
    code_diff: FlatTopoFileDiffDag | None,
    new_version_id: uuid.UUID,
    install_id: str | None,
) -> list:
    from database.models_enums import AutoDocConfigKind, VersionStatus
    from utils.db import get_version_by_id
    from utils.synthesis.deep_context import (
        DeepContextDoc,
        DeepContextDocKind,
    )
    from utils.synthesis.deep_context_prompts import (
        ARCHITECTURE_OVERVIEW_INTENT,
        LLM_ONBOARDING_INTENT,
    )

    new_version = await get_version_by_id(new_version_id)
    root_node_id = new_version.root_node.id

    if old_version_content and code_diff:
        print(
            f"Updating deep context docs for new version ({new_version_id}) from old version ({old_version_id})"
        )
        # TODO: Fix, actually pull this data from storage when we have it. Mirroring what is done
        # TODO: in `run_autodoc` when possible or empty if lost (e.g., the sources list and config
        # TODO: content supposed to contain the TOML as a string).
        update_set = {
            ContentKind.DEEP_CONTEXT_ARCHITECTURE,
            ContentKind.DEEP_CONTEXT_LLM_ONBOARDING,
        }

        update_tasks = [
            doc.update_from_diff(diff_collection=code_diff)
            for doc in old_version_content
            if doc.doc_kind in update_set
        ]
        completed_docs = await asyncio.gather(*update_tasks)
        # TODO: Add functionality to update the change log.
    else:
        run_autodoc = modal.Function.from_name(app_name="autodocs", name="run_autodoc")

        print("Creating deep context docs for version:", new_version_id)
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
                user_context="MEDIUM",
                content_kind=ContentKind.DEEP_CONTEXT_LLM_ONBOARDING,
            ),
        ]
        if install_id is not None:
            deep_context_doc_tasks.append(
                make_changelog.remote.aio(
                    version_id=new_version_id,
                    install_id=install_id,
                )
            )
        completed_docs = []

        for (
            content_kind,
            title,
            user_context_str,
            sources,
            config_content,
            doc_content,
        ) in await asyncio.gather(*deep_context_doc_tasks):
            if content_kind == ContentKind.DEEP_CONTEXT_CHANGELOG:
                # Skip changelog, it's handled separately
                print(f"Skipping changelog for content kind: {content_kind}")
                continue
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
        version_id=new_version_id,
        status=VersionStatus.GENERATION_COMPLETE,
    )

    return completed_docs
