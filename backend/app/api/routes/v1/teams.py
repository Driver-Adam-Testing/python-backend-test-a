"""API routes for Team management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.routes.v1 import team_members, team_sources
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_org_action, enforce_team_action
from app.schemas.team_schema import (
    CreateTeamRequest,
    TeamDetailResponse,
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
    """Request fields:
    - **name**: Team name (required, must be unique within organization)
    - **members**: Optional list of initial team members with roles
    """
    enforce_org_action(session, user, "team.admin")
    logger.info(f"User {user.user_id} creating team '{request.name}'")
    team_service = TeamService(session)
    return team_service.create_team(
        user=user,
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
    user_id: str | None = Query(
        default=None,
        description="Optional user ID to check if each team has this user as a member",
    ),
    source_id: UUID | None = Query(
        default=None,
        description="Optional source ID to check if each team has access to this source",
    ),
) -> TeamsResponse:
    """Super admins see all teams. Regular users only see teams they are members of."""
    enforce_org_action(session, user, "team.view")
    logger.info(
        f"User {user.user_id} listing teams (limit={limit}, offset={offset}, user_id={user_id}, source_id={source_id})"
    )
    team_service = TeamService(session)
    return team_service.get_teams(
        user=user,
        limit=limit,
        offset=offset,
        search=search,
        check_user_id=user_id,
        check_source_id=source_id,
    )


@router.get(
    "/search",
    response_model=TeamsResponse,
    summary="Search teams",
    description="Search for teams by name",
)
def search_teams(
    session: CurrentSession,
    user: UserToken,
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    user_id: str | None = Query(
        default=None,
        description="Optional user ID to check if each team has this user as a member",
    ),
    source_id: UUID | None = Query(
        default=None,
        description="Optional source ID to check if each team has access to this source",
    ),
) -> TeamsResponse:
    """Super admins see all teams. Regular users only see teams they are members of."""
    enforce_org_action(session, user, "team.view")
    logger.info(
        f"User {user.user_id} searching teams with query '{query}' (user_id={user_id}, source_id={source_id})"
    )
    team_service = TeamService(session)
    return team_service.get_teams(
        user=user,
        limit=limit,
        offset=offset,
        search=query,
        check_user_id=user_id,
        check_source_id=source_id,
    )


@router.get(
    "/{team_id}",
    response_model=TeamDetailResponse,
    summary="Get team by ID",
    description="Get details for a single team. User must be a member of the team.",
)
def get_team(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
) -> TeamDetailResponse:
    enforce_team_action(session, user, team_id, "team.view")
    logger.info(f"User {user.user_id} getting team {team_id}")
    team_service = TeamService(session)
    return team_service.get_team(
        user=user,
        team_id=team_id,
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
    """Request field: **name** - New team name (must be unique within organization)."""
    enforce_team_action(session, user, team_id, "team.manage")
    logger.info(f"User {user.user_id} updating team {team_id}")
    team_service = TeamService(session)
    return team_service.update_team(
        user=user,
        team_id=team_id,
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
    """Also removes all team memberships and source access grants."""
    enforce_org_action(session, user, "team.admin")
    logger.info(f"User {user.user_id} deleting team {team_id}")
    team_service = TeamService(session)
    team_service.delete_team(
        user=user,
        team_id=team_id,
    )
