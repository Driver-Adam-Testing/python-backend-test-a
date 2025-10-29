"""API routes for Source Teams (Source ACL) management - Teams only, not users."""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action
from app.schemas.source_access_schema import (
    AddSourceTeamsRequest,
    RemoveSourceTeamsRequest,
    SourceTeamsResponse,
    UpdateSourceTeamsRequest,
)
from app.services.source_access_service import SourceAccessService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/sources/{source_id}/teams",
    response_model=SourceTeamsResponse,
    summary="List source teams",
    description="Get paginated list of teams (not users) that have access to a source",
)
def get_source_teams(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    roles: list[str] | None = Query(
        default=None, description="Filter by roles: admin, member"
    ),
    search: str | None = Query(default=None, description="Search by team name"),
) -> SourceTeamsResponse:
    """
    Get paginated list of teams for a source.

    Returns only teams (not users) with their roles and access details.
    """
    enforce_asset_action(session, user, source_id, "asset.use_as_source")
    logger.info(
        f"User {user.user_id} getting teams for source {source_id} "
        f"(limit={limit}, offset={offset}, roles={roles}, search={search})"
    )
    service = SourceAccessService(session)
    return service.get_source_teams(
        user=user,
        source_id=source_id,
        roles=roles,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/sources/{source_id}/teams",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add teams to source",
    description="Grant teams access to a source with specific roles",
)
def add_source_teams(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: AddSourceTeamsRequest,
) -> None:
    """
    Add teams to a source.

    - **teams**: List of teams with roles to grant
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} adding {len(request.teams)} teams to source {source_id}"
    )
    service = SourceAccessService(session)
    service.add_source_teams(
        user=user,
        source_id=source_id,
        request=request,
    )


@router.put(
    "/sources/{source_id}/teams",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update source team roles",
    description="Update roles for source's existing teams",
)
def update_source_teams(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: UpdateSourceTeamsRequest,
) -> None:
    """
    Update roles for source's teams.

    - **teams**: List of teams with updated roles
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} updating {len(request.teams)} teams for source {source_id}"
    )
    service = SourceAccessService(session)
    service.update_source_teams(
        user=user,
        source_id=source_id,
        request=request,
    )


@router.delete(
    "/sources/{source_id}/teams",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove teams from source",
    description="Revoke team access to a source",
)
def remove_source_teams(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: RemoveSourceTeamsRequest,
) -> None:
    """
    Remove teams from a source.

    - **team_ids**: List of team IDs to remove
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} removing {len(request.team_ids)} teams from source {source_id}"
    )
    service = SourceAccessService(session)
    service.remove_source_teams(
        user=user,
        source_id=source_id,
        request=request,
    )
