"""Service for Team business logic."""

import logging
from datetime import datetime
from uuid import UUID, uuid4

from database.models import PrimaryAssetRoleGrant, Team, TeamMembership
from database.models_enums import TeamRole
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.repositories.base_repository import BaseRepository
from app.repositories.team_repository import TeamRepository
from app.schemas.team_schema import (
    CreateTeamRequest,
    TeamMemberInput,
    TeamResponse,
    TeamsListResponse,
    UpdateTeamRequest,
)

logger = logging.getLogger(__name__)


def map_team_role_to_backend(role: str) -> TeamRole:
    """Map frontend role string to backend TeamRole enum."""
    mapping = {
        "admin": TeamRole.team_admin,
        "member": TeamRole.member,
    }
    if role not in mapping:
        raise ValueError(f"Invalid role: {role}")
    return mapping[role]


def map_team_role_to_frontend(role: TeamRole) -> str:
    """Map backend TeamRole enum to frontend string."""
    mapping = {
        TeamRole.team_admin: "admin",
        TeamRole.member: "member",
    }
    return mapping[role]


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
    created_at = team.created_at.isoformat() if hasattr(team, "created_at") and team.created_at else now_iso
    updated_at = team.updated_at.isoformat() if hasattr(team, "updated_at") and team.updated_at else now_iso

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
        self.team_repository = TeamRepository(session)
        self.team_membership_repository = BaseRepository(session, TeamMembership)
        self.acl_repository = BaseRepository(session, PrimaryAssetRoleGrant)

    def create_team(
        self,
        organization_id: str,
        request: CreateTeamRequest,
    ) -> TeamResponse:
        """
        Create a new team.

        Args:
            organization_id: Organization ID
            request: Create team request

        Returns:
            Created team with counts

        Raises:
            HTTPException: If team name already exists or validation fails
        """
        logger.info(f"Creating team '{request.name}' for organization {organization_id}")

        # Create team
        team = Team(
            id=uuid4(),
            organization_id=organization_id,
            name=request.name.strip(),
        )

        try:
            created_team = self.team_repository.create(team)
        except IntegrityError as e:
            self.session.rollback()
            if "duplicate key value violates unique constraint" in str(e.orig):
                logger.error(f"Team name '{request.name}' already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Team name '{request.name}' already exists in this organization",
                )
            logger.error(f"Unexpected error creating team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create team",
            )

        # Add members if provided
        if request.members:
            try:
                self._add_team_members(created_team.id, request.members)
            except Exception as e:
                # Rollback team creation if member addition fails
                self.session.rollback()
                logger.error(f"Failed to add members to team: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add team members",
                )

        # Get team with counts
        team_with_counts = self.team_repository.get_team_with_counts(
            created_team.id,
            organization_id,
        )

        if not team_with_counts:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created team",
            )

        logger.info(f"Team '{request.name}' created successfully with ID {created_team.id}")
        return team_dict_to_response(team_with_counts)

    def get_teams(
        self,
        organization_id: str,
        limit: int = 30,
        offset: int = 0,
    ) -> TeamsListResponse:
        """
        Get paginated list of teams.

        Args:
            organization_id: Organization ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of teams with total count
        """
        logger.info(
            f"Getting teams for organization {organization_id} (limit={limit}, offset={offset})"
        )

        teams_with_counts = self.team_repository.get_teams_with_counts(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )

        total = self.team_repository.count_teams(organization_id)

        teams = [team_dict_to_response(team_dict) for team_dict in teams_with_counts]

        logger.info(f"Found {len(teams)} teams (total: {total})")
        return TeamsListResponse(teams=teams, total=total)

    def get_team(
        self,
        team_id: UUID,
        organization_id: str,
    ) -> TeamResponse:
        """
        Get a single team by ID.

        Args:
            team_id: Team ID
            organization_id: Organization ID

        Returns:
            Team with counts

        Raises:
            HTTPException: If team not found
        """
        logger.info(f"Getting team {team_id} for organization {organization_id}")

        team_with_counts = self.team_repository.get_team_with_counts(
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
        team_id: UUID,
        organization_id: str,
        request: UpdateTeamRequest,
    ) -> TeamResponse:
        """
        Update a team's name.

        Args:
            team_id: Team ID
            organization_id: Organization ID
            request: Update team request

        Returns:
            Updated team with counts

        Raises:
            HTTPException: If team not found or name already exists
        """
        logger.info(f"Updating team {team_id} to name '{request.name}'")

        # Get existing team
        team = self.team_repository.get_by_conditions(
            [
                Team.id == team_id,
                Team.organization_id == organization_id,
            ]
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
                    detail=f"Team name '{request.name}' already exists in this organization",
                )
            logger.error(f"Unexpected error updating team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update team",
            )

        # Get updated team with counts
        team_with_counts = self.team_repository.get_team_with_counts(
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
        team_id: UUID,
        organization_id: str,
    ) -> None:
        """
        Delete a team and all its associations.

        Args:
            team_id: Team ID
            organization_id: Organization ID

        Raises:
            HTTPException: If team not found
        """
        logger.info(f"Deleting team {team_id}")

        # Verify team exists and belongs to organization
        team = self.team_repository.get_by_conditions(
            [
                Team.id == team_id,
                Team.organization_id == organization_id,
            ]
        )

        if not team:
            logger.error(f"Team {team_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        try:
            # Delete team (cascade will handle TeamMembership)
            self.session.delete(team)

            # Delete source grants for this team
            # Note: We could also use cascade, but being explicit here
            acl_grants = self.session.query(PrimaryAssetRoleGrant).filter(
                PrimaryAssetRoleGrant.team_id == team_id
            ).all()
            for grant in acl_grants:
                self.session.delete(grant)

            self.session.commit()
            logger.info(f"Team {team_id} deleted successfully")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete team {team_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete team",
            )

    def search_teams(
        self,
        organization_id: str,
        query: str,
        limit: int = 30,
        offset: int = 0,
    ) -> TeamsListResponse:
        """
        Search teams by name.

        Args:
            organization_id: Organization ID
            query: Search query (case-insensitive)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching teams with total count
        """
        logger.info(
            f"Searching teams for organization {organization_id} with query '{query}' "
            f"(limit={limit}, offset={offset})"
        )

        teams_with_counts = self.team_repository.search_teams_with_counts(
            organization_id=organization_id,
            query=query,
            limit=limit,
            offset=offset,
        )

        total = self.team_repository.count_teams_by_search(organization_id, query)

        teams = [team_dict_to_response(team_dict) for team_dict in teams_with_counts]

        logger.info(f"Found {len(teams)} teams matching query (total: {total})")
        return TeamsListResponse(teams=teams, total=total)

    def _add_team_members(
        self,
        team_id: UUID,
        members: list[TeamMemberInput],
    ) -> None:
        """
        Add members to a team (internal helper).

        Args:
            team_id: Team ID
            members: List of members to add
        """
        for member in members:
            team_role = map_team_role_to_backend(member.role)
            membership = TeamMembership(
                id=uuid4(),
                team_id=team_id,
                user_id=member.userId,
                role=team_role,
            )
            self.session.add(membership)

        self.session.commit()
