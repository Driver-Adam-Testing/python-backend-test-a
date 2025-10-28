"""API routes for Team Member management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.schemas.team_member_schema import (
    AddTeamMembersRequest,
    RemoveTeamMembersRequest,
    TeamMembersResponse,
    UpdateTeamMembersRequest,
)
from app.services.team_member_service import TeamMemberService
from app.authorization.fastapi import enforce_team_action

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/{team_id}/members",
    response_model=TeamMembersResponse,
    summary="List team members",
    description=(
        "Get a paginated list of members for a specific team " "with optional filtering"
    ),
)
def list_team_members(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    roles: list[str] | None = Query(
        default=None,
        description="Filter by roles (admin, member)",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        description="Search by name or email",
    ),
) -> TeamMembersResponse:
    """
    Get paginated list of team members.

    Returns members with user details and team role.

    **Filtering:**
    - `roles`: Filter by team role (admin, member)
    - `search`: Search by user name or email (case-insensitive)
    """
    enforce_team_action(session, user, team_id, "team.view")
    logger.info(
        f"User {user.user_id} listing members for team {team_id} "
        f"(roles={roles}, search={search}, limit={limit}, offset={offset})"
    )
    team_member_service = TeamMemberService(session)
    return team_member_service.get_team_members(
        user=user,
        team_id=team_id,
        roles=roles,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{team_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add team members",
    description="Add new members to a team",
)
def add_team_members(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    request: AddTeamMembersRequest,
) -> None:
    """
    Add members to a team.

    - **members**: List of user IDs and their roles to add

    **Note:** Users must already exist in the system.
    """
    enforce_team_action(session, user, team_id, "team.manage")
    logger.info(
        f"User {user.user_id} adding {len(request.members)} members to team {team_id}"
    )
    team_member_service = TeamMemberService(session)
    team_member_service.add_team_members(
        user=user,
        team_id=team_id,
        request=request,
    )


@router.put(
    "/{team_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update team member roles",
    description="Update roles for existing team members",
)
def update_team_members(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    request: UpdateTeamMembersRequest,
) -> None:
    """
    Update roles for existing team members.

    - **members**: List of user IDs and their new roles

    **Note:** All users must already be members of the team.
    """
    enforce_team_action(session, user, team_id, "team.manage")
    logger.info(
        f"User {user.user_id} updating {len(request.members)} members in team {team_id}"
    )
    team_member_service = TeamMemberService(session)
    team_member_service.update_team_members(
        user=user,
        team_id=team_id,
        request=request,
    )


@router.delete(
    "/{team_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove team members",
    description="Remove members from a team",
)
def remove_team_members(
    session: CurrentSession,
    user: UserToken,
    team_id: UUID,
    request: RemoveTeamMembersRequest,
) -> None:
    """
    Remove members from a team.

    - **user_ids**: List of user IDs to remove from the team
    """
    enforce_team_action(session, user, team_id, "team.manage")
    logger.info(
        f"User {user.user_id} removing {len(request.user_ids)} members "
        f"from team {team_id}"
    )
    team_member_service = TeamMemberService(session)
    team_member_service.remove_team_members(
        user=user,
        team_id=team_id,
        request=request,
    )
