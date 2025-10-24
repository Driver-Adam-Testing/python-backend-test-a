"""API routes for Team management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.routes.v1 import team_members, team_sources
from app.api.session import CurrentSession
from app.schemas.team_schema import (
    CreateTeamRequest,
    TeamResponse,
    TeamsResponse,
    UpdateTeamRequest,
)
from app.services.team_service import TeamService

router = APIRouter()
logger = logging.getLogger(__name__)

# Include team members routes
router.include_router(team_members.router, tags=["team-members"])

# Include team sources routes
router.include_router(team_sources.router, tags=["team-sources"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TeamResponse,
    summary="Create a new team",
    description="Create a new team with optional initial members",
)
def create_team(
    session: CurrentSession,
    user: UserToken,
    request: CreateTeamRequest,
) -> TeamResponse:
    """
    Create a new team.

    - **name**: Team name (required, must be unique within organization)
    - **members**: Optional list of initial team members with roles
    """
    logger.info(f"User {user.user_id} creating team '{request.name}'")
    team_service = TeamService(session)
    return team_service.create_team(
        organization_id=user.organization_id,
        request=request,
    )


@router.get(
    "/",
    response_model=TeamsResponse,
    summary="List teams",
    description="Get a paginated list of teams for the organization with optional search",
)
def list_teams(
    session: CurrentSession,
    user: UserToken,
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    search: str | None = Query(
        default=None, description="Optional search query to filter teams by name"
    ),
) -> TeamsResponse:
    """
    Get paginated list of teams.

    Returns teams with aggregated counts of admins, members, and sources.
    Optionally filter by team name using the search parameter.
    """
    logger.info(
        f"User {user.user_id} listing teams "
        f"(limit={limit}, offset={offset}, search={search})"
    )
    team_service = TeamService(session)
    return team_service.get_teams(
        organization_id=user.organization_id,
        limit=limit,
        offset=offset,
        search=search,
    )


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get team by ID",
    description="Get details for a single team",
)
def get_team(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
) -> TeamResponse:
    """
    Get a single team by ID.

    Returns team with aggregated counts of admins, members, and sources.
    """
    logger.info(f"User {user.user_id} getting team {team_id}")
    team_service = TeamService(session)
    return team_service.get_team(
        team_id=team_id,
        organization_id=user.organization_id,
    )


@router.put(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Update team",
    description="Update a team's name",
)
def update_team(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    request: UpdateTeamRequest,
) -> TeamResponse:
    """
    Update a team's name.

    - **name**: New team name (required, must be unique within organization)
    """
    logger.info(f"User {user.user_id} updating team {team_id}")
    team_service = TeamService(session)
    return team_service.update_team(
        team_id=team_id,
        organization_id=user.organization_id,
        request=request,
    )


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete team",
    description="Delete a team and all its associations",
)
def delete_team(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
) -> None:
    """
    Delete a team.

    This will also remove:
    - All team memberships
    - All source access grants for this team
    """
    logger.info(f"User {user.user_id} deleting team {team_id}")
    team_service = TeamService(session)
    team_service.delete_team(
        team_id=team_id,
        organization_id=user.organization_id,
    )
