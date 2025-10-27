"""API routes for Team Sources (Team ACL) management."""

import logging
from uuid import UUID
import uuid

from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.schemas.source_access_schema import (
    AddTeamSourcesRequest,
    RemoveTeamSourcesRequest,
    TeamSourcesResponse,
    UpdateTeamSourcesRequest,
)
from app.services.source_access_service import SourceAccessService
from app.authorization.fastapi import enforce_asset_action, enforce_team_action

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/{team_id}/sources",
    response_model=TeamSourcesResponse,
    summary="List team sources",
    description="Get paginated list of sources (codebases/files) that a team has access to",
)
def get_team_sources(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    roles: list[str] | None = Query(
        default=None, description="Filter by roles: admin, member"
    ),
    visibilities: list[str] | None = Query(
        default=None, description="Filter by visibility: private, internal, public"
    ),
    search: str | None = Query(default=None, description="Search by display name"),
) -> TeamSourcesResponse:
    """
    Get paginated list of sources for a team.

    Returns sources with role and visibility information.
    """
    enforce_team_action(session, user, team_id, "team.view")
    logger.info(
        f"User {user.user_id} getting sources for team {team_id} "
        f"(limit={limit}, offset={offset}, roles={roles}, search={search})"
    )
    service = SourceAccessService(session)
    return service.get_team_sources(
        user=user,
        team_id=team_id,
        roles=roles,
        visibilities=visibilities,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{team_id}/sources",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add sources to team",
    description="Grant team access to sources with specific roles",
)
def add_team_sources(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    request: AddTeamSourcesRequest,
) -> None:
    """
    Add sources to a team.

    - **sources**: List of sources with roles to grant
    """
    enforce_team_action(session, user, team_id, "team.manage")
    for source in request.sources:
        enforce_asset_action(
            session,
            user,
            uuid.UUID(source.source_id),
            "asset.manage",
        )
    logger.info(
        f"User {user.user_id} adding {len(request.sources)} sources to team {team_id}"
    )
    service = SourceAccessService(session)
    service.add_team_sources(
        user=user,
        team_id=team_id,
        request=request,
    )


@router.put(
    "/{team_id}/sources",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update team source roles",
    description="Update roles for team's existing sources",
)
def update_team_sources(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    request: UpdateTeamSourcesRequest,
) -> None:
    """
    Update roles for team's sources.

    - **sources**: List of sources with updated roles
    """
    enforce_team_action(session, user, team_id, "team.manage")
    for source in request.sources:
        enforce_asset_action(
            session,
            user,
            uuid.UUID(source.source_id),
            "asset.manage",
        )
    logger.info(
        f"User {user.user_id} updating {len(request.sources)} sources for team {team_id}"
    )
    service = SourceAccessService(session)
    service.update_team_sources(
        user=user,
        team_id=team_id,
        request=request,
    )


@router.delete(
    "/{team_id}/sources",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove sources from team",
    description="Revoke team access to sources",
)
def remove_team_sources(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    request: RemoveTeamSourcesRequest,
) -> None:
    """
    Remove sources from a team.

    - **source_ids**: List of source IDs to remove
    """
    enforce_team_action(session, user, team_id, "team.manage")
    for source_id in request.source_ids:
        enforce_asset_action(
            session,
            user,
            uuid.UUID(source_id),
            "asset.manage",
        )
    logger.info(
        f"User {user.user_id} removing {len(request.source_ids)} sources from team {team_id}"
    )
    service = SourceAccessService(session)
    service.remove_team_sources(
        user=user,
        team_id=team_id,
        request=request,
    )
