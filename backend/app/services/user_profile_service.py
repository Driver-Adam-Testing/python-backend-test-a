"""Service for User Profile business logic."""

import logging

from database.models import OrgMembership
from database.models import User as DbUser
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.auth.models import User
from app.authorization.core import check_source_admin, check_team_admin
from app.schemas.user_profile_schema import MeResponse

logger = logging.getLogger(__name__)


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

        # Check if user is team admin
        is_team_admin = check_team_admin(self.session, user_id, organization_id)

        # Check if user has source admin role
        is_source_admin = check_source_admin(self.session, user_id, organization_id)

        return MeResponse(
            id=db_user.id,
            email=db_user.email or "",
            name=db_user.name or "",
            organization_id=organization_id,
            org_role=org_membership.role,
            entitlements=None,
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
