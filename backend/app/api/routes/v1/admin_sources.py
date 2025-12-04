"""API routes for Admin Sources management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_any_source_admin
from app.schemas.admin_sources_schema import AdminSourcesResponse, SourceVisibility
from app.services.admin_sources_service import AdminSourcesService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=AdminSourcesResponse,
    summary="Get admin sources list",
    description="Get paginated list of sources where the user has effective admin role. Excludes Pages (only returns Codebases and PDFs).",
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
    visibility: list[SourceVisibility] | None = Query(
        default=None, description="Filter by visibility"
    ),
    sort_by: str = Query(default="updated_at", description="Sort field"),
    sort_direction: str = Query(
        default="DESC",
        description="Sort direction",
        pattern="^(ASC|DESC)$",
    ),
    user_id: str | None = Query(
        default=None,
        description="Optional user ID to check if each source has direct access from this user",
    ),
    team_id: UUID | None = Query(
        default=None,
        description="Optional team ID to check if each source has access from this team",
    ),
) -> AdminSourcesResponse:
    enforce_any_source_admin(session, user)
    logger.info(
        f"User {user.user_id} getting admin sources "
        f"(limit={limit}, offset={offset}, search={search}, user_id={user_id}, team_id={team_id})"
    )
    service = AdminSourcesService(session)
    return service.get_admin_sources(
        user=user,
        search=search,
        kinds=kind,
        tag_ids=tag_ids,
        visibility=visibility,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
        offset=offset,
        check_user_id=user_id,
        check_team_id=team_id,
    )
