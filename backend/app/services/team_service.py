"""Service for Team business logic."""

import logging
from datetime import datetime
from uuid import UUID, uuid4

from database.models import PrimaryAssetRoleGrant, Team, TeamMembership
from database.models import User as DbUser
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth.models import User
from app.repositories import org_membership_repository, team_repository
from app.schemas.team_schema import (
    CreateTeamRequest,
    TeamMemberInput,
    TeamResponse,
    TeamsResponse,
    UpdateTeamRequest,
)

logger = logging.getLogger(__name__)


def get_user_by_id(session: Session, user_id: str) -> DbUser | None:
    """Get a user by ID."""
    query = select(DbUser).where(DbUser.id == user_id)
    return session.exec(query).first()


def team_dict_to_response(team_dict: dict) -> TeamResponse:
    """
    Convert team dictionary with counts to TeamResponse.

    Args:
        team_dict: Dictionary with 'team', 'admins', 'members', 'sources' keys

    Returns:
        TeamResponse object
    """
    team = team_dict["team"]

    # Handle created_at and updated_at
    # For now, use defaults if fields don't exist (until migration is run)
    now_iso = datetime.utcnow().isoformat()
    created_at = (
        team.created_at.isoformat()
        if hasattr(team, "created_at") and team.created_at
        else now_iso
    )
    updated_at = (
        team.updated_at.isoformat()
        if hasattr(team, "updated_at") and team.updated_at
        else now_iso
    )

    return TeamResponse(
        id=str(team.id),
        name=team.name,
        admins=team_dict["admins"],
        members=team_dict["members"],
        sources=team_dict["sources"],
        created_at=created_at,
        updated_at=updated_at,
    )


class TeamService:
    """Service for Team operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_team(
        self,
        user: User,
        request: CreateTeamRequest,
    ) -> TeamResponse:
        """
        Create a new team.

        Args:
            user: Authenticated user making the request
            request: Create team request

        Returns:
            Created team with counts

        Raises:
            HTTPException: If team name already exists or validation fails
        """
        organization_id = user.organization_id
        logger.info(
            f"Creating team '{request.name}' for organization {organization_id} by user {user.user_id}"
        )

        # Create team
        team = Team(
            id=uuid4(),
            organization_id=organization_id,
            name=request.name.strip(),
        )

        try:
            created_team = team_repository.create_team(self.session, team)
        except IntegrityError as e:
            self.session.rollback()
            if "duplicate key value violates unique constraint" in str(e.orig):
                logger.error(f"Team name '{request.name}' already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Team name '{request.name}' already exists "
                        f"in this organization"
                    ),
                )
            logger.error(f"Unexpected error creating team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create team",
            )

        # Add members if provided
        if request.members:
            try:
                self._add_team_members(
                    created_team.id, organization_id, request.members
                )
            except ValueError as e:
                # Rollback team creation if member validation fails
                self.session.rollback()
                logger.error(f"Member validation failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )
            except Exception as e:
                # Rollback team creation if member addition fails
                self.session.rollback()
                logger.error(f"Failed to add members to team: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add team members",
                )

        # Get team with counts
        team_with_counts = team_repository.get_team_with_counts(
            self.session,
            created_team.id,
            organization_id,
        )

        if not team_with_counts:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created team",
            )

        logger.info(
            f"Team '{request.name}' created successfully with ID {created_team.id}"
        )
        return team_dict_to_response(team_with_counts)

    def get_teams(
        self,
        user: User,
        limit: int = 30,
        offset: int = 0,
        search: str | None = None,
    ) -> TeamsResponse:
        """
        Get paginated list of teams with optional search.

        Args:
            user: Authenticated user making the request
            limit: Maximum number of results
            offset: Number of results to skip
            search: Optional search query to filter teams by name

        Returns:
            List of teams with total count
        """
        organization_id = user.organization_id
        logger.info(
            f"Getting teams for organization {organization_id} by user {user.user_id} "
            f"(limit={limit}, offset={offset}, search={search})"
        )

        # If search is provided and not empty, use search function
        if search and search.strip():
            teams_with_counts = team_repository.search_teams_with_counts(
                session=self.session,
                organization_id=organization_id,
                query=search,
                limit=limit,
                offset=offset,
            )

            total = team_repository.count_teams_by_search(
                session=self.session,
                organization_id=organization_id,
                search_query=search,
            )
        else:
            # Otherwise, get all teams
            teams_with_counts = team_repository.get_teams_with_counts(
                session=self.session,
                organization_id=organization_id,
                limit=limit,
                offset=offset,
            )

            total = team_repository.count_teams(
                session=self.session,
                organization_id=organization_id,
            )

        teams = [team_dict_to_response(team_dict) for team_dict in teams_with_counts]

        logger.info(f"Found {len(teams)} teams (total: {total})")
        return TeamsResponse(teams=teams, total=total)

    def get_team(
        self,
        user: User,
        team_id: UUID,
    ) -> TeamResponse:
        """
        Get a single team by ID.

        Args:
            user: Authenticated user making the request
            team_id: Team ID

        Returns:
            Team with counts

        Raises:
            HTTPException: If team not found
        """
        organization_id = user.organization_id
        logger.info(
            f"Getting team {team_id} for organization {organization_id} by user {user.user_id}"
        )

        team_with_counts = team_repository.get_team_with_counts(
            session=self.session,
            team_id=team_id,
            organization_id=organization_id,
        )

        if not team_with_counts:
            logger.error(f"Team {team_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        return team_dict_to_response(team_with_counts)

    def update_team(
        self,
        user: User,
        team_id: UUID,
        request: UpdateTeamRequest,
    ) -> TeamResponse:
        """
        Update a team's name.

        Args:
            user: Authenticated user making the request
            team_id: Team ID
            request: Update team request

        Returns:
            Updated team with counts

        Raises:
            HTTPException: If team not found or name already exists
        """
        organization_id = user.organization_id
        logger.info(
            f"Updating team {team_id} to name '{request.name}' by user {user.user_id}"
        )

        # Get existing team
        team = team_repository.get_team_by_id(
            session=self.session,
            team_id=team_id,
            organization_id=organization_id,
        )

        if not team:
            logger.error(f"Team {team_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        # Update team
        team.name = request.name.strip()

        try:
            self.session.add(team)
            self.session.commit()
            self.session.refresh(team)
        except IntegrityError as e:
            self.session.rollback()
            if "duplicate key value violates unique constraint" in str(e.orig):
                logger.error(f"Team name '{request.name}' already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Team name '{request.name}' already exists "
                        f"in this organization"
                    ),
                )
            logger.error(f"Unexpected error updating team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update team",
            )

        # Get updated team with counts
        team_with_counts = team_repository.get_team_with_counts(
            session=self.session,
            team_id=team_id,
            organization_id=organization_id,
        )

        if not team_with_counts:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated team",
            )

        logger.info(f"Team {team_id} updated successfully")
        return team_dict_to_response(team_with_counts)

    def delete_team(
        self,
        user: User,
        team_id: UUID,
    ) -> None:
        """
        Delete a team and all its associations.

        Args:
            user: Authenticated user making the request
            team_id: Team ID

        Raises:
            HTTPException: If team not found
        """
        organization_id = user.organization_id
        logger.info(f"Deleting team {team_id} by user {user.user_id}")

        # Verify team exists and belongs to organization
        team = team_repository.get_team_by_id(
            session=self.session,
            team_id=team_id,
            organization_id=organization_id,
        )

        if not team:
            logger.error(f"Team {team_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        try:
            # Delete source grants for this team
            acl_grants = (
                self.session.query(PrimaryAssetRoleGrant)
                .filter(PrimaryAssetRoleGrant.team_id == team_id)
                .all()
            )
            for grant in acl_grants:
                self.session.delete(grant)

            # Delete team (cascade will handle TeamMembership)
            team_repository.delete_team(self.session, team)
            logger.info(f"Team {team_id} deleted successfully")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete team {team_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete team",
            )

    def _add_team_members(
        self,
        team_id: UUID,
        organization_id: str,
        members: list[TeamMemberInput],
    ) -> None:
        """
        Add members to a team (internal helper).

        Args:
            team_id: Team ID
            organization_id: Organization ID
            members: List of members to add

        Raises:
            ValueError: If user not found or not in organization
        """
        for member in members:
            # Validate user exists
            user = get_user_by_id(self.session, member.user_id)
            if not user:
                raise ValueError(f"User {member.user_id} not found")

            # Validate user belongs to organization
            if not org_membership_repository.check_user_in_organization(
                self.session, member.user_id, organization_id
            ):
                raise ValueError(
                    f"User {member.user_id} is not a member of this organization"
                )

            membership = TeamMembership(
                id=uuid4(),
                team_id=team_id,
                user_id=member.user_id,
                role=member.role,
            )
            self.session.add(membership)

        self.session.commit()
