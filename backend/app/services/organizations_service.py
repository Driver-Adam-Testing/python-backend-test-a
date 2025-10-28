"""Service for Organization business logic."""

import logging

from database.models_enums import OrgRole
from fastapi import HTTPException
from sqlmodel import Session

from app.api.auth import UserToken
from app.repositories.user_repository import (
    count_organization_super_admins,
    delete_organization_membership,
    get_organization_membership,
    update_organization_role,
)
from app.schemas.auth0_schema import SetUserRoleResponse
from app.services.auth0_factory import create_auth0_service

logger = logging.getLogger(__name__)


class OrganizationsService:
    """Service for Organization member operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def delete_member(
        self,
        user: UserToken,
        user_id: str,
    ) -> None:
        """
        Delete a member from an organization.

        Validates that:
        - User exists in the organization
        - At least one super_admin remains after deletion

        Deletes from Auth0 first, then from database to ensure consistency.

        Args:
            user: Authenticated user token (for organization context)
            user_id: ID of user to delete

        Raises:
            HTTPException: 404 if user not found in organization
            HTTPException: 403 if removing last super_admin
            Exception: If Auth0 or database deletion fails
        """
        membership = get_organization_membership(
            self.session, user_id, user.organization_id
        )
        if not membership:
            raise HTTPException(
                404, f"User {user_id} is not a member of this organization"
            )

        # Check if removing last super_admin
        if membership.role == OrgRole.super_admin:
            super_admin_count = count_organization_super_admins(
                self.session, user.organization_id
            )
            if super_admin_count <= 1:
                raise HTTPException(
                    403,
                    "Cannot remove the last super_admin from the organization. "
                    "At least one super_admin is required.",
                )

        # Delete from Auth0 first
        auth0_service = create_auth0_service()
        auth0_service.delete_user_from_organization(user, user_id)

        # Only delete from database if Auth0 deletion succeeded
        delete_organization_membership(self.session, membership)

    def update_member_role(
        self,
        user: UserToken,
        modified_user_id: str,
        new_role: str,
    ) -> SetUserRoleResponse:
        """
        Update a member's role in an organization.

        Validates that:
        - User exists in the organization
        - Role is valid (handled by repository layer)

        Args:
            user: Authenticated user token (for organization context)
            modified_user_id: ID of user whose role to update
            new_role: New role value (e.g., 'super_admin', 'member')

        Returns:
            SetUserRoleResponse with user_id, organization_id, and role

        Raises:
            HTTPException: 404 if user not found in organization
            ValueError: If role is invalid (raised by repository)
        """
        membership = get_organization_membership(
            self.session, modified_user_id, user.organization_id
        )
        if not membership:
            raise HTTPException(
                404, f"User {modified_user_id} is not a member of this organization"
            )

        # Update role (validation happens in repository function)
        update_organization_role(
            self.session, modified_user_id, user.organization_id, new_role
        )

        # Return the new role with org context
        return SetUserRoleResponse(
            user_id=modified_user_id,
            organization_id=user.organization_id,
            role=new_role,
        )
