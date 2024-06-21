from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
import modal
from app.api.session import CurrentSession

router = APIRouter()

class Onboarding(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"

class OnboardingRequestBody(BaseModel):
    creator_id: str
    org_id: str
    workspace_id: str
    download_url: str
    object_key: str

@router.post(
    "/",
    summary="Trigger Codebase Onboarding",
    response_description="Return HTTP Status Code 200 (OK)",
)
def trigger_onboarding(session: CurrentSession, trigger_body: OnboardingRequestBody) -> Onboarding:
    """
    ## Trigger codebase onboarding
    Returns:
        Onboarding: Returns a JSON response with the health status
    """

    # For Endpoint
    # codebases/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/first_nes.zip
    archive_name = Path(trigger_body.object_key).name
    onboard_and_inspect = modal.Function.lookup("codebase-onboarding", "onboard_and_inspect")
    onboard_and_inspect.remote(trigger_body.download_url, archive_name, trigger_body.org_id, trigger_body.creator_id, trigger_body.workspace_id)
    return Onboarding(status="OK")