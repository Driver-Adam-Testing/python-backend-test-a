"""API routes for Member Search (Users + Teams)."""

import logging

from fastapi import APIRouter, Query

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.schemas.rbac_search_schema import MemberSearchResponse
from app.services.rbac_search_service import RBACSearchService
from app.authorization.fastapi import enforce_org_actions

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/search",
    response_model=MemberSearchResponse,
    summary="Search members (users and teams)",
    description="Search for members (both users and teams) across the organization",
)
def search_members(
    session: CurrentSession,
    user: UserToken,
    query: str = Query(..., min_length=1, description="Search query for name or email"),
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
) -> MemberSearchResponse:
    """
    Search for members (users and teams) within the organization.

    Returns combined results from users (by name/email) and teams (by name).
    Used for adding members to sources.
    """
    enforce_org_actions(session, user, ["users.view", "team.view"])
    logger.info(
        f"User {user.user_id} searching for members with query '{query}' "
        f"(limit={limit}, offset={offset})"
    )
    service = RBACSearchService(session)
    return service.search_members(
        user=user,
        query=query,
        limit=limit,
        offset=offset,
    )
