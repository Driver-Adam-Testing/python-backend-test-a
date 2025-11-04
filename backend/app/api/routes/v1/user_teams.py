"""API routes for User Teams management."""

import logging

from database.models_enums import PrimaryAssetRole
from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.schemas.user_schema import (
    AddUserTeamsRequest,
    OrganizationMembersResponse,
    RemoveUserTeamsRequest,
    UpdateUserTeamsRequest,
    UserTeamsResponse,
)
from app.services.user_service import UserService
from app.authorization.fastapi import enforce_org_action, enforce_super_admin, enforce_team_action

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/search",
    response_model=OrganizationMembersResponse,
    summary="Search organization users",
    description="Search for users within the organization by name or email",
)
def search_organization_users(
    session: CurrentSession,
    user: UserToken,
    query: str = Query(..., min_length=1, description="Search query for name or email"),
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
) -> OrganizationMembersResponse:
    """
    Search for users within the organization.

    Returns users matching the search query by name or email.
    """
    enforce_org_action(session, user, "users.view")
    logger.info(
        f"User {user.user_id} searching for users with query '{query}' "
        f"(limit={limit}, offset={offset})"
    )
    service = UserService(session)
    return service.search_organization_users(
        user=user,
        query=query,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{user_id}/teams",
    response_model=UserTeamsResponse,
    summary="Get user's teams",
    description="Get paginated list of teams that a user belongs to",
)
def get_user_teams(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    roles: list[PrimaryAssetRole] | None = Query(
        default=None, description="Filter by roles: asset_admin, asset_member"
    ),
    search: str | None = Query(default=None, description="Search by team name"),
) -> UserTeamsResponse:
    """
    Get paginated list of teams for a user.

    Returns teams with role and count information.
    """
    enforce_super_admin(session, user)
    logger.info(
        f"User {user.user_id} getting teams for user {user_id} "
        f"(limit={limit}, offset={offset}, roles={roles}, search={search})"
    )
    service = UserService(session)
    return service.get_user_teams(
        user=user,
        user_id=user_id,
        roles=roles,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{user_id}/teams",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add user to teams",
    description="Add user to teams with specific roles",
)
def add_user_teams(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
    request: AddUserTeamsRequest,
) -> None:
    """
    Add user to teams.

    - **teams**: List of teams with roles to add user to
    """
    enforce_super_admin(session, user)
    logger.info(
        f"User {user.user_id} adding user {user_id} to {len(request.teams)} teams"
    )
    service = UserService(session)
    service.add_user_teams(
        user=user,
        user_id=user_id,
        request=request,
    )


@router.put(
    "/{user_id}/teams",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update user's team roles",
    description="Update roles for user's existing teams",
)
def update_user_teams(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
    request: UpdateUserTeamsRequest,
) -> None:
    """
    Update user's team roles.

    - **teams**: List of teams with updated roles
    """
    enforce_super_admin(session, user)
    logger.info(
        f"User {user.user_id} updating roles for user {user_id} in {len(request.teams)} teams"
    )
    service = UserService(session)
    service.update_user_teams(
        user=user,
        user_id=user_id,
        request=request,
    )


@router.delete(
    "/{user_id}/teams",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove user from teams",
    description="Remove user from specified teams",
)
def remove_user_teams(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
    request: RemoveUserTeamsRequest,
) -> None:
    """
    Remove user from teams.

    - **team_ids**: List of team IDs to remove user from
    """
    enforce_super_admin(session, user)
    logger.info(
        f"User {user.user_id} removing user {user_id} from {len(request.team_ids)} teams"
    )
    service = UserService(session)
    service.remove_user_teams(
        user=user,
        user_id=user_id,
        request=request,
    )
