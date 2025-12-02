"""Service for Source Access (ACL) business logic."""

import logging
from uuid import UUID

from database.models import PrimaryAsset, PrimaryAssetRoleGrant, Team
from database.models_enums import PrimaryAssetRole, PrincipalKind, TeamRole
from fastapi import HTTPException, status
from shared.authorization.helpers import is_super_admin
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.auth.models import User
from app.repositories import acl_repository, team_member_repository, team_repository
from app.schemas.source_access_schema import (
    AddSourceTeamsRequest,
    AddSourceUsersRequest,
    AddTeamSourcesRequest,
    RemoveSourceTeamsRequest,
    RemoveSourceUsersRequest,
    RemoveTeamSourcesRequest,
    SourceTeamInput,
    SourceTeamResponse,
    SourceTeamsResponse,
    SourceUserInput,
    SourceUserResponse,
    SourceUsersResponse,
    SourceVisibility,
    TeamMembershipInfo,
    TeamSourceInput,
    TeamSourceResponse,
    TeamSourcesResponse,
    UpdateSourceTeamsRequest,
    UpdateSourceUsersRequest,
    UpdateTeamSourcesRequest,
)
from app.schemas.user_schema import AssignmentType

logger = logging.getLogger(__name__)


def grant_to_team_source_response(
    grant: PrimaryAssetRoleGrant,
    asset: PrimaryAsset,
    visibility: SourceVisibility,
    effective_role: PrimaryAssetRole | None,
) -> TeamSourceResponse:
    is_browsable = (
        asset.most_recent_version.browsable if asset.most_recent_version else False
    )

    return TeamSourceResponse(
        id=str(asset.id),
        organization_id=asset.organization_id,
        kind=asset.kind.value,
        display_name=asset.display_name,
        provider=asset.provider.value if asset.provider else None,
        created_at=asset.created_at.isoformat() if asset.created_at else "",
        updated_at=asset.updated_at.isoformat() if asset.updated_at else "",
        role=grant.role,
        visibility=visibility,
        team_id=grant.team_id,
        is_browsable=is_browsable,
        effective_role=effective_role,
    )


def build_source_team_response(
    session: Session,
    grant: PrimaryAssetRoleGrant,
    team: Team,
    organization_id: str,
    user_team_role: TeamRole | None,
    is_user_super_admin: bool,
) -> SourceTeamResponse:
    """
    Build SourceTeamResponse with team information and user's effective role.

    Args:
        session: Database session for fetching additional data
        grant: PrimaryAssetRoleGrant instance
        team: Team instance
        organization_id: Organization ID
        user_team_role: User's role in the team (pre-fetched, None if not a member)
        is_user_super_admin: Whether current user is a super admin

    Returns:
        SourceTeamResponse object with team details and effective role
    """
    member_count = team_member_repository.count_team_members(
        session=session,
        team_id=team.id,
        organization_id=organization_id,
    )

    effective_team_role = TeamRole.team_admin if is_user_super_admin else user_team_role

    return SourceTeamResponse(
        team_id=team.id,
        team_name=team.name,
        role=grant.role,
        member_count=member_count,
        created_at=grant.created_at.isoformat() if grant.created_at else "",
        effective_team_role=effective_team_role,
    )


class SourceAccessService:
    """Service for Source Access (ACL) operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ===== Team Sources Methods =====

    def get_team_sources(
        self,
        user: User,
        team_id: UUID,
        roles: list[PrimaryAssetRole] | None = None,
        visibilities: list[str] | None = None,
        search: str | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> TeamSourcesResponse:
        """
        Get paginated list of sources for a team.

        Args:
            user: Authenticated user making the request
            team_id: Team ID
            roles: Optional list of roles to filter by
            visibilities: Optional list of visibilities to filter by
            search: Optional search query
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of team sources with total count

        Raises:
            HTTPException: If team not found
        """
        organization_id = user.organization_id
        logger.info(
            f"Getting sources for team {team_id} (roles={roles}, "
            f"visibilities={visibilities}, search={search})"
        )

        # Verify team exists
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

        sources_with_details = acl_repository.get_team_sources_with_details(
            session=self.session,
            team_id=team_id,
            organization_id=organization_id,
            roles=roles,
            visibilities=visibilities,
            search=search,
            limit=limit,
            offset=offset,
        )

        total = acl_repository.count_team_sources(
            session=self.session,
            team_id=team_id,
            organization_id=organization_id,
            roles=roles,
            visibilities=visibilities,
            search=search,
        )

        asset_ids = [item["asset"].id for item in sources_with_details]
        effective_roles = acl_repository.get_user_effective_roles_for_assets_batch(
            session=self.session,
            user_id=user.user_id,
            organization_id=organization_id,
            asset_ids=asset_ids,
        )

        sources = [
            grant_to_team_source_response(
                item["grant"],
                item["asset"],
                item["visibility"],
                effective_roles.get(item["asset"].id),
            )
            for item in sources_with_details
        ]

        logger.info(f"Found {len(sources)} sources (total: {total})")
        return TeamSourcesResponse(sources=sources, total=total)

    def add_team_sources(
        self,
        user: User,
        team_id: UUID,
        request: AddTeamSourcesRequest,
    ) -> None:
        """
        Add sources to a team.

        Args:
            user: Authenticated user making the request
            team_id: Team ID
            request: Add team sources request

        Raises:
            HTTPException: If team or source not found, or grant already exists
        """
        organization_id = user.organization_id
        logger.info(
            f"Adding {len(request.sources)} sources to team {team_id} by user {user.user_id}"
        )

        # Verify team exists
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

        # Verify all sources exist
        for source in request.sources:
            asset = acl_repository.get_primary_asset_by_id(
                self.session,
                UUID(source.source_id),
                organization_id,
            )
            if not asset:
                logger.error(f"Source {source.source_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source {source.source_id} not found",
                )

        # Add sources
        try:
            self._add_sources_to_team(team_id, organization_id, request.sources)
            self.session.commit()
            logger.info(f"Successfully added {len(request.sources)} sources to team")
        except IntegrityError as e:
            self.session.rollback()
            if "duplicate key value violates unique constraint" in str(e.orig):
                logger.error("One or more sources already assigned to team")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more sources are already assigned to this team",
                )
            logger.error(f"Unexpected error adding sources: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add sources to team",
            )

    def update_team_sources(
        self,
        user: User,
        team_id: UUID,
        request: UpdateTeamSourcesRequest,
    ) -> None:
        """
        Update roles for team sources.

        Args:
            user: Authenticated user making the request
            team_id: Team ID
            request: Update team sources request

        Raises:
            HTTPException: If team or grant not found
        """
        organization_id = user.organization_id
        logger.info(
            f"Updating {len(request.sources)} sources for team {team_id} by user {user.user_id}"
        )

        # Verify team exists
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

        # Update each source's role
        for source in request.sources:
            grant = acl_repository.get_grant_by_team_and_asset(
                session=self.session,
                team_id=team_id,
                primary_asset_id=UUID(source.source_id),
            )
            if not grant:
                logger.error(
                    f"Source {source.source_id} not assigned to team {team_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source {source.source_id} is not assigned to this team",
                )

            grant.role = source.role
            self.session.add(grant)

        try:
            self.session.commit()
            logger.info(f"Successfully updated {len(request.sources)} sources")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update team sources: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update team sources",
            )

    def remove_team_sources(
        self,
        user: User,
        team_id: UUID,
        request: RemoveTeamSourcesRequest,
    ) -> None:
        """
        Remove sources from a team.

        Args:
            user: Authenticated user making the request
            team_id: Team ID
            request: Remove team sources request

        Raises:
            HTTPException: If team not found
        """
        organization_id = user.organization_id
        logger.info(f"Removing {len(request.source_ids)} sources from team {team_id}")

        # Verify team exists
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

        # Remove sources
        removed_count = 0
        for source_id in request.source_ids:
            grant = acl_repository.get_grant_by_team_and_asset(
                session=self.session,
                team_id=team_id,
                primary_asset_id=UUID(source_id),
            )
            if grant:
                self.session.delete(grant)
                removed_count += 1

        try:
            self.session.commit()
            logger.info(f"Successfully removed {removed_count} sources from team")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to remove team sources: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove team sources",
            )

    # ===== Source Users Methods =====

    def get_source_users(
        self,
        user: User,
        source_id: UUID,
        roles: list[PrimaryAssetRole] | None = None,
        search: str | None = None,
        assignment_type: AssignmentType | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> SourceUsersResponse:
        """
        Get paginated list of users for a source.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            roles: Optional list of roles to filter by
            search: Optional search query
            assignment_type: Optional assignment type filter ('direct' or 'inherited')
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of source users with total count

        Raises:
            HTTPException: If source not found
        """
        organization_id = user.organization_id
        logger.info(
            f"Getting users for source {source_id} by user {user.user_id} "
            f"(roles={roles}, search={search}, assignment_type={assignment_type})"
        )

        # Verify source exists
        asset = acl_repository.get_primary_asset_by_id(
            self.session,
            source_id,
            organization_id,
        )

        if not asset:
            logger.error(f"Source {source_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found",
            )

        # Get users with all details in single optimized query
        users_data = acl_repository.get_source_users_with_details(
            session=self.session,
            primary_asset_id=source_id,
            organization_id=organization_id,
            roles=roles,
            search=search,
            assignment_type=assignment_type,
            limit=limit,
            offset=offset,
        )

        # Get total count using optimized query
        total = acl_repository.count_source_users(
            session=self.session,
            primary_asset_id=source_id,
            organization_id=organization_id,
            roles=roles,
            search=search,
            assignment_type=assignment_type,
        )

        # Batch fetch team memberships for all users
        user_ids = [data["user_id"] for data in users_data]
        teams_by_user = acl_repository.get_source_team_memberships_batch(
            session=self.session,
            source_id=source_id,
            user_ids=user_ids,
            organization_id=organization_id,
        )

        # Build response objects directly from repository data
        users = [
            SourceUserResponse(
                user_id=data["user_id"],
                name=data["name"],
                email=data["email"],
                picture="",
                created_at=data["created_at"],
                is_super_admin=data["is_super_admin"],
                # Granular role breakdown
                user_org_role=data["user_org_role"],
                asset_org_role=data["asset_org_role"],
                team_source_role=data["team_source_role"],
                effective_role=data["effective_role"],
                source_role=data["user_grant_role"],
                teams=[
                    TeamMembershipInfo(**team_data)
                    for team_data in teams_by_user.get(data["user_id"], [])
                ],
            )
            for data in users_data
        ]

        logger.info(f"Found {len(users)} users (total: {total})")
        return SourceUsersResponse(users=users, total=total)

    def get_source_teams(
        self,
        user: User,
        source_id: UUID,
        roles: list[PrimaryAssetRole] | None = None,
        search: str | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> SourceTeamsResponse:
        """
        Get paginated list of teams for a source.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            roles: Optional list of roles to filter by
            search: Optional search query
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of source teams with total count

        Raises:
            HTTPException: If source not found
        """
        organization_id = user.organization_id
        user_id = user.user_id
        logger.info(
            f"Getting teams for source {source_id} by user {user_id} (roles={roles}, search={search})"
        )

        # Verify source exists
        asset = acl_repository.get_primary_asset_by_id(
            self.session,
            source_id,
            organization_id,
        )

        if not asset:
            logger.error(f"Source {source_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found",
            )

        is_user_super_admin = is_super_admin(self.session, user_id, organization_id)

        teams_with_details = acl_repository.get_source_teams_with_details(
            session=self.session,
            primary_asset_id=source_id,
            organization_id=organization_id,
            user_id=user_id,
            roles=roles,
            search=search,
            limit=limit,
            offset=offset,
        )

        total = acl_repository.count_source_teams(
            session=self.session,
            primary_asset_id=source_id,
            organization_id=organization_id,
            roles=roles,
            search=search,
        )

        teams = [
            build_source_team_response(
                session=self.session,
                grant=item["grant"],
                team=item["member"],
                organization_id=organization_id,
                user_team_role=item["user_team_role"],
                is_user_super_admin=is_user_super_admin,
            )
            for item in teams_with_details
        ]

        logger.info(f"Found {len(teams)} teams (total: {total})")
        return SourceTeamsResponse(teams=teams, total=total)

    def add_source_users(
        self,
        user: User,
        source_id: UUID,
        request: AddSourceUsersRequest,
    ) -> None:
        """
        Add users to a source.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            request: Add source users request

        Raises:
            HTTPException: If source or user not found, or grant already exists
        """
        organization_id = user.organization_id
        logger.info(f"Adding {len(request.users)} users to source {source_id}")

        # Verify source exists
        asset = acl_repository.get_primary_asset_by_id(
            self.session,
            source_id,
            organization_id,
        )

        if not asset:
            logger.error(f"Source {source_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found",
            )

        # Add users
        try:
            self._add_users_to_source(source_id, organization_id, request.users)
            self.session.commit()
            logger.info(f"Successfully added {len(request.users)} users to source")
        except IntegrityError as e:
            self.session.rollback()
            if "duplicate key value violates unique constraint" in str(e.orig):
                logger.error("One or more users already have access to source")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more users already have access to this source",
                )
            logger.error(f"Unexpected error adding users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add users to source",
            )

    def update_source_users(
        self,
        user: User,
        source_id: UUID,
        request: UpdateSourceUsersRequest,
    ) -> None:
        """
        Update roles for source users.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            request: Update source users request

        Raises:
            HTTPException: If source or grant not found
        """
        organization_id = user.organization_id
        logger.info(f"Updating {len(request.users)} users for source {source_id}")

        # Verify source exists
        asset = acl_repository.get_primary_asset_by_id(
            self.session,
            source_id,
            organization_id,
        )

        if not asset:
            logger.error(f"Source {source_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found",
            )

        # Update each user's role
        for user_input in request.users:
            grant = acl_repository.get_grant_by_user_and_asset(
                session=self.session,
                user_id=user_input.user_id,
                primary_asset_id=source_id,
            )

            if not grant:
                logger.error(
                    f"User {user_input.user_id} does not have access to source {source_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_input.user_id} does not have access to this source",
                )

            grant.role = user_input.role
            self.session.add(grant)

        try:
            self.session.commit()
            logger.info(f"Successfully updated {len(request.users)} users")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update source users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update source users",
            )

    def remove_source_users(
        self,
        user: User,
        source_id: UUID,
        request: RemoveSourceUsersRequest,
    ) -> None:
        """
        Remove users from a source.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            request: Remove source users request

        Raises:
            HTTPException: If source not found
        """
        organization_id = user.organization_id
        logger.info(f"Removing {len(request.user_ids)} users from source {source_id}")

        # Verify source exists
        asset = acl_repository.get_primary_asset_by_id(
            self.session,
            source_id,
            organization_id,
        )

        if not asset:
            logger.error(f"Source {source_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found",
            )

        # Remove users
        removed_count = 0
        for user_id in request.user_ids:
            grant = acl_repository.get_grant_by_user_and_asset(
                session=self.session,
                user_id=user_id,
                primary_asset_id=source_id,
            )

            if grant:
                self.session.delete(grant)
                removed_count += 1

        try:
            self.session.commit()
            logger.info(f"Successfully removed {removed_count} users from source")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to remove source users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove source users",
            )

    def add_source_teams(
        self,
        user: User,
        source_id: UUID,
        request: AddSourceTeamsRequest,
    ) -> None:
        """
        Add teams to a source.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            request: Add source teams request

        Raises:
            HTTPException: If source or team not found, or grant already exists
        """
        organization_id = user.organization_id
        logger.info(f"Adding {len(request.teams)} teams to source {source_id}")

        # Verify source exists
        asset = acl_repository.get_primary_asset_by_id(
            self.session,
            source_id,
            organization_id,
        )

        if not asset:
            logger.error(f"Source {source_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found",
            )

        # Add teams
        try:
            self._add_teams_to_source(source_id, organization_id, request.teams)
            self.session.commit()
            logger.info(f"Successfully added {len(request.teams)} teams to source")
        except IntegrityError as e:
            self.session.rollback()
            if "duplicate key value violates unique constraint" in str(e.orig):
                logger.error("One or more teams already have access to source")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more teams already have access to this source",
                )
            logger.error(f"Unexpected error adding teams: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add teams to source",
            )

    def update_source_teams(
        self,
        user: User,
        source_id: UUID,
        request: UpdateSourceTeamsRequest,
    ) -> None:
        """
        Update roles for source teams.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            request: Update source teams request

        Raises:
            HTTPException: If source or grant not found
        """
        organization_id = user.organization_id
        logger.info(f"Updating {len(request.teams)} teams for source {source_id}")

        # Verify source exists
        asset = acl_repository.get_primary_asset_by_id(
            self.session,
            source_id,
            organization_id,
        )

        if not asset:
            logger.error(f"Source {source_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found",
            )

        # Update each team's role
        for team_input in request.teams:
            # Verify team exists in organization
            team = team_repository.get_team_by_id(
                session=self.session,
                team_id=team_input.team_id,
                organization_id=organization_id,
            )

            if not team:
                logger.error(f"Team {team_input.team_id} not found in organization")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Team {team_input.team_id} not found",
                )

            grant = acl_repository.get_grant_by_team_and_asset(
                session=self.session,
                team_id=team_input.team_id,
                primary_asset_id=source_id,
            )

            if not grant:
                logger.error(
                    f"Team {team_input.team_id} does not have access to source {source_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Team {team_input.team_id} does not have access to this source",
                )

            grant.role = team_input.role
            self.session.add(grant)

        try:
            self.session.commit()
            logger.info(f"Successfully updated {len(request.teams)} teams")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update source teams: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update source teams",
            )

    def remove_source_teams(
        self,
        user: User,
        source_id: UUID,
        request: RemoveSourceTeamsRequest,
    ) -> None:
        """
        Remove teams from a source.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            request: Remove source teams request

        Raises:
            HTTPException: If source not found
        """
        organization_id = user.organization_id
        logger.info(f"Removing {len(request.team_ids)} teams from source {source_id}")

        # Verify source exists
        asset = acl_repository.get_primary_asset_by_id(
            self.session,
            source_id,
            organization_id,
        )

        if not asset:
            logger.error(f"Source {source_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found",
            )

        # Remove teams
        removed_count = 0
        for team_id in request.team_ids:
            grant = acl_repository.get_grant_by_team_and_asset(
                session=self.session,
                team_id=team_id,
                primary_asset_id=source_id,
            )

            if grant:
                self.session.delete(grant)
                removed_count += 1

        try:
            self.session.commit()
            logger.info(f"Successfully removed {removed_count} teams from source")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to remove source teams: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove source teams",
            )

    # ===== Private Helper Methods =====

    def _add_sources_to_team(
        self,
        team_id: UUID,
        organization_id: str,
        sources: list[TeamSourceInput],
    ) -> None:
        """
        Add sources to a team (internal helper).

        Args:
            team_id: Team ID
            organization_id: Organization ID
            sources: List of sources to add
        """
        for source in sources:
            grant = PrimaryAssetRoleGrant(
                primary_asset_id=UUID(source.source_id),
                organization_id=organization_id,
                principal_kind=PrincipalKind.team,
                team_id=team_id,
                user_id=None,
                role=source.role,
            )
            self.session.add(grant)

    def _add_users_to_source(
        self,
        source_id: UUID,
        organization_id: str,
        users: list[SourceUserInput],
    ) -> None:
        """
        Add users (not teams) to a source (internal helper).

        Args:
            source_id: Source (primary asset) ID
            organization_id: Organization ID
            users: List of users to add
        """
        for user_input in users:
            grant = PrimaryAssetRoleGrant(
                primary_asset_id=source_id,
                organization_id=organization_id,
                principal_kind=PrincipalKind.user,
                user_id=user_input.user_id,
                team_id=None,
                role=user_input.role,
            )

            self.session.add(grant)

    def _add_teams_to_source(
        self,
        source_id: UUID,
        organization_id: str,
        teams: list[SourceTeamInput],
    ) -> None:
        """
        Add teams to a source (internal helper).

        Args:
            source_id: Source (primary asset) ID
            organization_id: Organization ID
            teams: List of teams to add
        """
        for team_input in teams:
            # Verify team exists in organization
            team = team_repository.get_team_by_id(
                session=self.session,
                team_id=team_input.team_id,
                organization_id=organization_id,
            )

            if not team:
                logger.error(f"Team {team_input.team_id} not found in organization")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Team {team_input.team_id} not found",
                )

            grant = PrimaryAssetRoleGrant(
                primary_asset_id=source_id,
                organization_id=organization_id,
                principal_kind=PrincipalKind.team,
                team_id=team_input.team_id,
                user_id=None,
                role=team_input.role,
            )

            self.session.add(grant)
