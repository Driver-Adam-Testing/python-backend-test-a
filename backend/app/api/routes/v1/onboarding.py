import logging
import uuid
from pathlib import Path

import modal
from fastapi import APIRouter
from pydantic import BaseModel

from app.api.auth import M2MToken
from app.api.session import CurrentSession
from app.core.config import settings

router = APIRouter()


class CodebaseConnection(BaseModel):
    # TODO: Is the status being consumed somewhere? Otherwise this isn't appropriate.
    status: str = "OK"
    call_id: str | None = None


class CodebaseConnectionRequest(BaseModel):
    org_id: str | None = None
    download_url: str
    object_key: str
    version_id: uuid.UUID
    provider: str | None = None


@router.post(
    "/",
    summary="Trigger Codebase Connection",
    response_description="Return HTTP Status Code 200 (OK)",
)
def trigger_codebase_connection(
    current_token: M2MToken,
    session: CurrentSession,
    trigger_body: CodebaseConnectionRequest,
) -> CodebaseConnection:
    archive_name = Path(trigger_body.object_key).name
    logging.info(
        f"Triggering codebase connection for org = {trigger_body.org_id} and archive = {archive_name}, provider = {trigger_body.provider}, version_id = {trigger_body.version_id}"
    )
    run_codebase_connection = modal.Function.lookup(
        "inspector-v2",
        "run_codebase_connection",
        environment_name=settings.MODAL_ENVIRONMENT,
    )

    call = run_codebase_connection.spawn(
        presigned_url=trigger_body.download_url,
        archive_name=archive_name,
        org_id=trigger_body.org_id,
        version_id=trigger_body.version_id,
        provider=trigger_body.provider,
    )

    return CodebaseConnection(status="OK", call_id=call.object_id)


class PdfOnboardingRequestBody(BaseModel):
    node_id: str | None = None


@router.post(
    "/generate-pdf-summaries",
    summary="Trigger PDF Summarization and Embedding",
    response_description="Return HTTP Status Code 200 (OK)",
)
def trigger_pdf_summary_processing(
    current_token: M2MToken, session: CurrentSession, body: PdfOnboardingRequestBody
) -> CodebaseConnection:
    logging.info("Triggering pdf summary creation...")
    # archive_name = Path(trigger_body.object_key).name
    create_and_embed_pdf_summaries = modal.Function.lookup(
        app_name="pdf-summary-embedding",
        # TODO: this line is not need once we deploy to production.
        environment_name=settings.MODAL_ENVIRONMENT,
        tag="create_and_embed_pdf_summaries",
    )
    call = create_and_embed_pdf_summaries.spawn(body.node_id)

    return CodebaseConnection(status="OK", call_id=call.object_id)
