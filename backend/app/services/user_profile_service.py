"""Service for User Profile business logic."""

import logging

from database.models import (
    Organization,
    OrgMembership,
    PrimaryAssetRoleGrant,
    TeamMembership,
)
from database.models import User as DbUser
from database.models_enums import OrgRole, PrimaryAssetRole, PrincipalKind, TeamRole
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.auth.models import User
from app.schemas.user_profile_schema import Entitlement, MeResponse

logger = logging.getLogger(__name__)


def map_org_role_to_string(role: OrgRole) -> str:
    """Map OrgRole enum to string."""
    return role.value


class UserProfileService:
    """Service for User Profile operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_current_user_profile(self, user: User) -> MeResponse:
        """
        Get the current user's profile information.

        Args:
            user: Authenticated user from JWT token

        Returns:
            MeResponse with user profile data

        Raises:
            HTTPException: If user not found in database
        """
        user_id = user.user_id
        organization_id = user.organization_id

        # Query User table
        db_user = self._get_user_from_db(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found in database",
            )

        # Query OrgMembership for role
        org_membership = self._get_org_membership(user_id, organization_id)
        if not org_membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not a member of organization {organization_id}",
            )

        # Get entitlements from organization metadata
        entitlements = self._get_entitlements(organization_id)

        # Check if user is team admin
        is_team_admin = self._check_team_admin(user_id, organization_id)

        # Check if user has source admin role
        is_source_admin = self._check_source_admin(user_id, organization_id)

        return MeResponse(
            id=db_user.id,
            email=db_user.email or "",
            name=db_user.name or "",
            organization_id=organization_id,
            org_role=map_org_role_to_string(org_membership.role),
            entitlements=entitlements,
            team_admin=is_team_admin,
            source_admin=is_source_admin,
        )

    def _get_user_from_db(self, user_id: str) -> DbUser | None:
        """Get user from database by user_id."""
        query = select(DbUser).where(DbUser.id == user_id)
        return self.session.exec(query).first()

    def _get_org_membership(
        self, user_id: str, organization_id: str
    ) -> OrgMembership | None:
        """Get organization membership for user."""
        query = select(OrgMembership).where(
            OrgMembership.user_id == user_id,
            OrgMembership.org_id == organization_id,
        )
        return self.session.exec(query).first()

    def _get_entitlements(self, organization_id: str) -> list[Entitlement] | None:
        """
        Get entitlements from organization metadata.

        Returns None if no entitlements or organization not found.
        """
        query = select(Organization).where(Organization.id == organization_id)
        org = self.session.exec(query).first()

        if not org or not org.org_metadata:
            return None

        # Extract entitlements from org_metadata if present
        entitlements_data = org.org_metadata.get("entitlements")
        if not entitlements_data or not isinstance(entitlements_data, list):
            return None

        # Convert to Entitlement objects
        entitlements = []
        for item in entitlements_data:
            if isinstance(item, dict) and "name" in item and "enabled" in item:
                entitlements.append(
                    Entitlement(name=item["name"], enabled=item["enabled"])
                )

        return entitlements if entitlements else None

    def _check_team_admin(self, user_id: str, organization_id: str) -> bool:
        """
        Check if user is admin of ANY team.

        Returns True if user has TeamRole.team_admin in at least one team.
        Note: TeamMembership doesn't have organization_id, so we filter by user_id only.
        """
        query = (
            select(TeamMembership)
            .where(
                TeamMembership.user_id == user_id,
                TeamMembership.role == TeamRole.team_admin,
            )
            .limit(1)
        )
        result = self.session.exec(query).first()
        return result is not None

    def _check_source_admin(self, user_id: str, organization_id: str) -> bool:
        """
        Check if user has admin role for ANY source (direct grant).

        Returns True if user has PrimaryAssetRole.admin for at least one source
        where principal_kind='user'.
        """
        query = (
            select(PrimaryAssetRoleGrant)
            .where(
                PrimaryAssetRoleGrant.user_id == user_id,
                PrimaryAssetRoleGrant.organization_id == organization_id,
                PrimaryAssetRoleGrant.principal_kind == PrincipalKind.user,
                PrimaryAssetRoleGrant.role == PrimaryAssetRole.asset_admin,
            )
            .limit(1)
        )
        result = self.session.exec(query).first()
        return result is not None
