"""
This file exposes the modal (https://www.modal.com) interface for the comprehender package.
"""

import json
import traceback
from datetime import datetime

import modal
from sqlmodel import Session, select

app = modal.App("comprehender")


# Note, all these schenanigans are required because `poetry_install_from_file` doesn't install our comprehender-database
# package, which is a *local* package in pyproject.toml of comprehender.
image = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file("pyproject.toml")
)

comprehender_modal_config = {
    "image": image,
    "mounts": [
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
    ],
    "secrets": [
        modal.Secret.from_name("driver-api-credentials"),
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("db"),
    ],
    "proxy": modal.Proxy.from_name("pg-proxy"),
    "concurrency_limit": 5,
    "region": "us-east",
}


@app.function(timeout=3600, **comprehender_modal_config, keep_warm=1)
def create_app_note(
    workspace_id: str,
    codebase_id: str,
    prompt: str,
    echoed_context: dict[str, any],
    options: dict | None = None,
):
    from shared.pipelines.create_app_note import (
        CreateAppNoteRequest,
        create_app_note,
    )

    if options is None:
        options = {}
    request = CreateAppNoteRequest(
        workspace_id=workspace_id,
        prompt=prompt,
        codebase_id=codebase_id,
        options=options,
    )
    derived_content_id = echoed_context.pop("document_id")
    errors = None
    try:
        result = create_app_note(request)
    except Exception as e:
        print(f"Exception occurred: {e}")
        traceback.print_exc()
        errors = [f"Error in create_app_note: {e}"]
        result = {}
    save_app_note_results(
        derived_content_id=derived_content_id,
        results=result,
        prompt=prompt,
        echoed_context=echoed_context,
        errors=errors,
    )
    return result


@app.function(timeout=20 * 60, **comprehender_modal_config, keep_warm=1)
def single_shot_edit(
    workspace_id: str, codebase_id: str, prompt: str, options: dict = None
):
    from shared.pipelines.run_agent import RunAgentRequest, run_agent

    if options is None:
        options = {}
    singleshot = run_agent(
        RunAgentRequest(
            workspace_id=workspace_id,
            codebase_id=codebase_id,
            prompt=prompt,
            options=options,
        )
    )
    return {
        "name": "singleshot expansion",
        "content": singleshot,
        "description": "description",
    }


@app.function(timeout=60, **comprehender_modal_config)
def upload_auxiliary_doc(workspace_id: str, codebase_id: str, url: str) -> str:
    from shared.pipelines.upload_file_to_open_ai import (
        upload_file_from_url_to_open_ai,
    )

    return upload_file_from_url_to_open_ai(
        workspace_id=workspace_id, codebase_id=codebase_id, file_url=url
    )


@app.function(
    timeout=3600 * 16,  # 16 hours
    **comprehender_modal_config,
)
def create_embeddings(workspace_id: str, codebase_id: str):
    embed_content_for_codebase = modal.Function.lookup(
        "embedding", "embed_content_for_codebase"
    )

    print(
        f"Loading tech docs into vector db for workspace `{workspace_id}` and codebase `{codebase_id}`."
    )
    embed_content_for_codebase.remote(codebase_id, workspace_id)


### TODO: This is the wrong place in general for db operations.
### When we migrate comprehender, look into changing this.
class ContentStatus:
    GENERATING = "generating"
    GENERATION_COMPLETE = "generation-complete"
    GENERATION_ERROR = "generation-error"


def save_app_note_results(
    derived_content_id: str,
    results: dict,
    prompt: str,
    errors: list | None = None,
    echoed_context: dict | None = None,
):
    from database.db import engine
    from database.models_v1 import DerivedContent

    with Session(engine) as session:
        derived_content = session.exec(
            select(DerivedContent).where(DerivedContent.id == derived_content_id)
        ).first()
        if not derived_content:
            raise Exception(f"No Derived content {derived_content_id}")
        if not derived_content.misc_metadata:
            derived_content.misc_metadata = {}

        ## TODO: LOTS OF REDUNDANT DATA HERE... I DON'T KNOW WHAT'S ACTUALLY USED, so I'm keeping everything
        ## TODO: Ensure dc_metadata is created here without assigning a whole object.
        derived_content.misc_metadata["generation_timestamp"] = str(datetime.now())
        derived_content.misc_metadata["document_id"] = derived_content_id
        derived_content.misc_metadata["content"] = results.get("content", "")
        derived_content.misc_metadata["errors"] = errors
        derived_content.misc_metadata["prompt"] = prompt
        derived_content.misc_metadata["name"] = results.get("name", "")
        derived_content.misc_metadata["extra_context"] = echoed_context
        if not derived_content.misc_metadata.get("history", None):
            derived_content.misc_metadata["history"] = []
        if not derived_content.misc_metadata.get("modal_context", None):
            derived_content.misc_metadata["modal_context"] = {}
        derived_content.misc_metadata["modal_context"]["callback"] = echoed_context

        action = (
            ContentStatus.GENERATION_ERROR
            if errors
            else ContentStatus.GENERATION_COMPLETE
        )
        derived_content.status = action
        data = (
            "\n".join([error for error in errors if isinstance(error, str)])
            if errors
            else results.get("content", None)
        )

        derived_content.misc_metadata["history"].append(
            {
                "action": action,
                "data": data,
                "timestamp": str(datetime.now()),
            }
        )
        try:
            existing_content = json.loads(derived_content.content)
        except Exception:
            existing_content = {}

        content = {}
        content["name"] = results.get("name", None) or existing_content.get(
            "name", None
        )
        content["content"] = results.get("content", None) or existing_content.get(
            "content", None
        )
        content["description"] = results.get(
            "description", None
        ) or existing_content.get("description", None)
        derived_content.content = json.dumps(content)
        session.add(derived_content)
        session.commit()
