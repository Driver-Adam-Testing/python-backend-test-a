"""API routes for Admin Sources management."""

import logging

from fastapi import APIRouter, Query

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.schemas.admin_sources_schema import AdminSourcesResponse
from app.services.admin_sources_service import AdminSourcesService
from app.authorization.fastapi import enforce_super_admin

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=AdminSourcesResponse,
    summary="Get admin sources list",
    description="Get paginated list of all sources with admin metadata including member and team counts",
)
def get_admin_sources(
    session: CurrentSession,
    user: UserToken,
    limit: int = Query(
        default=20, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    search: str | None = Query(default=None, description="Search by display name"),
    kind: list[str] | None = Query(default=None, description="Filter by asset type"),
    tag_ids: list[str] | None = Query(default=None, description="Filter by tag IDs"),
    sort_by: str = Query(default="updated_at", description="Sort field"),
    sort_direction: str = Query(
        default="DESC",
        description="Sort direction",
        pattern="^(ASC|DESC)$",
    ),
) -> AdminSourcesResponse:
    """
    Get paginated list of sources for admin management.

    Returns sources with visibility, member counts, and team counts.
    Supports filtering by search term, asset kind, and tags.
    """
    enforce_super_admin(session, user)
    logger.info(
        f"User {user.user_id} getting admin sources "
        f"(limit={limit}, offset={offset}, search={search})"
    )
    service = AdminSourcesService(session)
    return service.get_admin_sources(
        user=user,
        search=search,
        kinds=kind,
        tag_ids=tag_ids,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
        offset=offset,
    )
