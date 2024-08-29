import logging
import os
from pathlib import Path
from uuid import UUID

import modal
from fastapi import APIRouter
from pydantic import BaseModel

from app.api.auth import CurrentToken
from app.api.session import CurrentSession
from app.core.config import settings

router = APIRouter()


class Onboarding(BaseModel):
    # TODO: Is the status being consumed somewhere? Otherwise this isn't appropriate.
    status: str = "OK"
    call_id: str | None = None


class OnboardingRequestBody(BaseModel):
    creator_id: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None
    download_url: str
    object_key: str
    provider: str | None = None


@router.post(
    "/",
    summary="Trigger Codebase Onboarding",
    response_description="Return HTTP Status Code 200 (OK)",
)
def trigger_onboarding(
    current_token: CurrentToken,
    session: CurrentSession,
    trigger_body: OnboardingRequestBody,
) -> Onboarding:
    """
    ## Trigger codebase onboarding
    Returns:
        Onboarding: Returns a JSON response with the health status
    """

    logging.info("Triggering codebase onboarding...")
    logging.info(f"modal env = {os.getenv("MODAL_ENVIRONMENT")}")
    archive_name = Path(trigger_body.object_key).name
    onboard_and_inspect = modal.Function.lookup(
        "codebase-onboarding", "onboard_and_inspect"
    )
    call = onboard_and_inspect.spawn(
        trigger_body.download_url,
        archive_name,
        trigger_body.org_id,
        trigger_body.creator_id,
        UUID(trigger_body.workspace_id),
        trigger_body.provider,
    )

    return Onboarding(status="OK", call_id=call.object_id)


class PdfOnboardingRequestBody(BaseModel):
    source_content_id: str | None = None


@router.post(
    "/generate-pdf-summaries",
    summary="Trigger PDF Summarization and Embedding",
    response_description="Return HTTP Status Code 200 (OK)",
)
def trigger_pdf_summary_processing(
    current_token: CurrentToken, session: CurrentSession, body: PdfOnboardingRequestBody
) -> Onboarding:
    logging.info("Triggering pdf summary creation...")
    # archive_name = Path(trigger_body.object_key).name
    create_and_embed_pdf_summaries = modal.Function.lookup(
        app_name="pdf-summary-embedding",
        # TODO: this line is not need once we deploy to production.
        environment_name=settings.MODAL_ENVIRONMENT,
        tag="create_and_embed_pdf_summaries",
    )
    call = create_and_embed_pdf_summaries.spawn(body.source_content_id)

    return Onboarding(status="OK", call_id=call.object_id)
