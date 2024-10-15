"""
This file exposes the modal (https://www.modal.com) interface for the comprehender package.
"""

import json
import os
from datetime import datetime

import modal
from shared.interfaces.search import SearchInput, SearchResults
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
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("db"),
    ],
    "concurrency_limit": 5,
    "region": "us-east",
}

if os.environ["MODAL_ENVIRONMENT"] != "staging":
    comprehender_modal_config["proxy"] = modal.Proxy.from_name("pg-proxy")


@app.function(timeout=20 * 60, **comprehender_modal_config, keep_warm=1)
def single_shot_edit(
    workspace_id: str, codebase_id: str, prompt: str, options: dict | None = None
) -> dict[str, str]:
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
) -> None:
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
            else results.get("content")
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
        content["name"] = results.get("name") or existing_content.get("name", None)
        content["content"] = results.get("content") or existing_content.get(
            "content", None
        )
        content["description"] = results.get("description") or existing_content.get(
            "description", None
        )
        derived_content.content = json.dumps(content)
        session.add(derived_content)
        session.commit()


@app.function(timeout=3600, **comprehender_modal_config, keep_warm=3)
def search(input: dict | SearchInput) -> SearchResults:
    from database.db import engine
    from shared.pipelines.search import (
        SearchInput,
        search_content,
    )

    if isinstance(input, dict):
        input = SearchInput(**input)
    print(input.model_dump())
    with Session(engine) as session:
        return search_content(session, input=input)
