from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel
from app.api.auth import CurrentUser
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
def trigger_onboarding(session: CurrentSession, current_user: CurrentUser, trigger_body: OnboardingRequestBody) -> Onboarding:
    print(trigger_body)
    """
    ## Trigger codebase onboarding
    Returns:
        Onboarding: Returns a JSON response with the health status
    """
    return Onboarding(status="OK")