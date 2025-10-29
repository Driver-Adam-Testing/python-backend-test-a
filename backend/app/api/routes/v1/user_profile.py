"""API routes for User Profile management."""

import logging

from fastapi import APIRouter, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.schemas.user_profile_schema import MeResponse
from app.services.user_profile_service import UserProfileService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=MeResponse,
    summary="Get current user profile",
    description="Get the currently authenticated user's profile information",
)
def get_me(
    session: CurrentSession,
    user: UserToken,
) -> MeResponse:
    """
    Get the current user's profile.

    Returns:
    - **id**: User ID from Auth0
    - **email**: User email
    - **name**: User name
    - **organization_id**: Organization ID
    - **org_role**: Organization role (super_admin/member)
    - **entitlements**: List of entitlements or null
    - **team_admin**: True if user is admin of ANY team
    - **source_admin**: True if user has admin role for ANY source (direct grant)
    """
    logger.info(f"User {user.user_id} fetching their profile")
    service = UserProfileService(session)
    return service.get_current_user_profile(user)
