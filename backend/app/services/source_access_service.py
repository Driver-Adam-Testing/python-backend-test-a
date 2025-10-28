"""Service for Source Access (ACL) business logic."""

import logging
from uuid import UUID, uuid4

from database.models import PrimaryAsset, PrimaryAssetRoleGrant, Team
from database.models import User as DbUser
from database.models_enums import PrimaryAssetRole, PrincipalKind
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.auth.models import User
from app.repositories import acl_repository, team_repository
from app.schemas.source_access_schema import (
    AddSourceUsersRequest,
    AddTeamSourcesRequest,
    RemoveSourceUsersRequest,
    RemoveTeamSourcesRequest,
    SourceUserInput,
    SourceUserResponse,
    SourceUsersResponse,
    TeamMembershipInfo,
    TeamSourceInput,
    TeamSourceResponse,
    TeamSourcesResponse,
    UpdateSourceUsersRequest,
    UpdateTeamSourcesRequest,
)

logger = logging.getLogger(__name__)


def map_source_role_to_backend(role: str) -> PrimaryAssetRole:
    """Map frontend role string to backend PrimaryAssetRole enum."""
    mapping = {
        "admin": PrimaryAssetRole.admin,
        "member": PrimaryAssetRole.viewer,
    }
    if role not in mapping:
        raise ValueError(f"Invalid role: {role}")
    return mapping[role]


def map_source_role_to_frontend(role: PrimaryAssetRole) -> str:
    """Map backend PrimaryAssetRole enum to frontend string."""
    mapping = {
        PrimaryAssetRole.admin: "admin",
        PrimaryAssetRole.viewer: "member",
    }
    return mapping[role]


def grant_to_team_source_response(
    grant: PrimaryAssetRoleGrant, asset: PrimaryAsset
) -> TeamSourceResponse:
    """
    Convert grant and asset to TeamSourceResponse.

    Args:
        grant: PrimaryAssetRoleGrant instance
        asset: PrimaryAsset instance

    Returns:
        TeamSourceResponse object
    """
    return TeamSourceResponse(
        id=str(asset.id),
        organization_id=asset.organization_id,
        kind=asset.kind.value,
        display_name=asset.display_name,
        provider=asset.provider.value if asset.provider else None,
        created_at=asset.created_at.isoformat() if asset.created_at else "",
        updated_at=asset.updated_at.isoformat() if asset.updated_at else "",
        role=map_source_role_to_frontend(grant.role),
        visibility="private",  # TODO: Use actual visibility when field is added
        team_id=str(grant.team_id) if grant.team_id else "",
    )


def build_source_user_response(
    session: Session,
    grant: PrimaryAssetRoleGrant,
    user_or_team: DbUser | Team,
    kind: str,
    organization_id: str,
    source_id: UUID,
) -> SourceUserResponse:
    """
    Build SourceUserResponse with full user profile information.

    Args:
        session: Database session for fetching additional data
        grant: PrimaryAssetRoleGrant instance
        user_or_team: DbUser or Team instance
        kind: User kind ('user' or 'team')
        organization_id: Organization ID
        source_id: Source ID to filter teams by access

    Returns:
        SourceUserResponse object with user profile and team memberships
    """
    if kind == "user":
        user = user_or_team

        # Fetch user's org membership for role and super_admin status
        org_membership = acl_repository.get_user_org_membership(
            session=session,
            user_id=user.id,
            organization_id=organization_id,
        )

        is_super_admin = False
        user_role = "member"
        if org_membership:
            from database.models_enums import OrgRole

            is_super_admin = org_membership.role == OrgRole.super_admin
            user_role = org_membership.role.value

        # Fetch user's team memberships
        team_memberships_data = acl_repository.get_user_team_memberships(
            session=session,
            user_id=user.id,
            organization_id=organization_id,
        )

        # Get team IDs that have access to this source
        from sqlmodel import select

        team_ids_with_source_access = set(
            session.exec(
                select(PrimaryAssetRoleGrant.team_id).where(
                    PrimaryAssetRoleGrant.primary_asset_id == source_id,
                    PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
                    PrimaryAssetRoleGrant.team_id.is_not(None),
                    PrimaryAssetRoleGrant.organization_id == organization_id,
                )
            ).all()
        )

        # Build team membership list - only teams with access to this source
        teams = [
            TeamMembershipInfo(
                team_id=str(item["team"].id),
                display_name=item["team"].name,
                team_role=item["membership"].role.value,
            )
            for item in team_memberships_data
            if item["team"].id in team_ids_with_source_access
        ]

        return SourceUserResponse(
            user_id=user.id,
            name=user.name or "",
            email=user.email or "",
            picture="",  # TODO: Fetch from Auth0 or add to User model
            visibility="private",  # TODO: Use actual visibility
            created_at=grant.created_at.isoformat() if grant.created_at else "",
            is_super_admin=is_super_admin,
            user_role=user_role,
            teams=teams,
        )
    else:  # team
        team = user_or_team
        # For teams, return minimal user-like response (since schema is user-only now)
        return SourceUserResponse(
            user_id=str(team.id),
            name=team.name,
            email=None,
            picture=None,
            visibility="private",  # TODO: Use actual visibility
            created_at=grant.created_at.isoformat() if grant.created_at else "",
            is_super_admin=False,
            user_role="team",  # Indicate this is a team
            teams=[],  # Teams don't have team memberships
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
        roles: list[str] | None = None,
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

        sources = [
            grant_to_team_source_response(item["grant"], item["asset"])
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

            grant.role = map_source_role_to_backend(source.role)
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
        roles: list[str] | None = None,
        user_kind: str | None = None,
        search: str | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> SourceUsersResponse:
        """
        Get paginated list of users for a source.

        Args:
            user: Authenticated user making the request
            source_id: Source (primary asset) ID
            roles: Optional list of roles to filter by
            user_kind: Optional user kind filter
            search: Optional search query
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of source users with total count

        Raises:
            HTTPException: If source not found
        """
        organization_id = user.organization_id
        logger.info(
            f"Getting users for source {source_id} by user {user.user_id} (roles={roles}, "
            f"kind={user_kind}, search={search})"
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

        users_with_details = acl_repository.get_source_users_with_details(
            session=self.session,
            primary_asset_id=source_id,
            organization_id=organization_id,
            roles=roles,
            user_kind=user_kind,
            search=search,
            limit=limit,
            offset=offset,
        )

        total = acl_repository.count_source_users(
            session=self.session,
            primary_asset_id=source_id,
            organization_id=organization_id,
            roles=roles,
            user_kind=user_kind,
            search=search,
        )

        users = [
            build_source_user_response(
                session=self.session,
                grant=item["grant"],
                user_or_team=item["member"],
                kind=item["kind"],
                organization_id=organization_id,
                source_id=source_id,
            )
            for item in users_with_details
        ]

        logger.info(f"Found {len(users)} users (total: {total})")
        return SourceUsersResponse(users=users, total=total)

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
        for source_user in request.users:
            if source_user.kind == "user":
                grant = acl_repository.get_grant_by_user_and_asset(
                    session=self.session,
                    user_id=source_user.user_id,
                    primary_asset_id=source_id,
                )
            else:  # team
                grant = acl_repository.get_grant_by_team_and_asset(
                    session=self.session,
                    team_id=UUID(source_user.user_id),
                    primary_asset_id=source_id,
                )

            if not grant:
                logger.error(
                    f"User {source_user.user_id} ({source_user.kind}) does not have "
                    f"access to source {source_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {source_user.user_id} does not have access to this source",
                )

            grant.role = map_source_role_to_backend(source_user.role)
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
        logger.info(f"Removing {len(request.users)} users from source {source_id}")

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
        for source_user in request.users:
            if source_user.kind == "user":
                grant = acl_repository.get_grant_by_user_and_asset(
                    session=self.session,
                    user_id=source_user.user_id,
                    primary_asset_id=source_id,
                )
            else:  # team
                grant = acl_repository.get_grant_by_team_and_asset(
                    session=self.session,
                    team_id=UUID(source_user.user_id),
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
            role = map_source_role_to_backend(source.role)
            grant = PrimaryAssetRoleGrant(
                id=uuid4(),
                primary_asset_id=UUID(source.source_id),
                organization_id=organization_id,
                principal_kind=PrincipalKind.team,
                team_id=team_id,
                user_id=None,
                role=role,
            )
            self.session.add(grant)

    def _add_users_to_source(
        self,
        source_id: UUID,
        organization_id: str,
        users: list[SourceUserInput],
    ) -> None:
        """
        Add users to a source (internal helper).

        Args:
            source_id: Source (primary asset) ID
            organization_id: Organization ID
            users: List of users to add
        """
        for source_user in users:
            role = map_source_role_to_backend(source_user.role)

            if source_user.kind == "user":
                grant = PrimaryAssetRoleGrant(
                    id=uuid4(),
                    primary_asset_id=source_id,
                    organization_id=organization_id,
                    principal_kind=PrincipalKind.user,
                    user_id=source_user.user_id,
                    team_id=None,
                    role=role,
                )
            else:  # team
                grant = PrimaryAssetRoleGrant(
                    id=uuid4(),
                    primary_asset_id=source_id,
                    organization_id=organization_id,
                    principal_kind=PrincipalKind.team,
                    team_id=UUID(source_user.user_id),
                    user_id=None,
                    role=role,
                )

            self.session.add(grant)
