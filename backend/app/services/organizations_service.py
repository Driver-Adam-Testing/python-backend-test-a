"""Service for Organization business logic."""

import logging

from database.models_enums import OrgRole
from fastapi import HTTPException
from sqlmodel import Session

from app.api.auth import UserToken
from app.repositories.org_membership_repository import (
    bulk_update_organization_roles,
    list_organization_members,
)
from app.repositories.user_repository import (
    count_organization_super_admins,
    delete_organization_membership,
    get_organization_membership,
    update_organization_role,
)
from app.schemas.organization_schema import (
    BulkSetUserRoleInput,
    BulkSetUserRoleResponse,
    ListMembersResponse,
    OrganizationMember,
    SetUserRoleResponse,
)
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
        if membership.role == OrgRole.org_super_admin:
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
        new_role: OrgRole,
    ) -> SetUserRoleResponse:
        """
        Update a member's role in an organization.

        Validates that:
        - User exists in the organization
        - Role is valid (handled by Pydantic validation)

        Args:
            user: Authenticated user token (for organization context)
            modified_user_id: ID of user whose role to update
            new_role: New role enum value

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

        # Update role
        update_organization_role(
            self.session, modified_user_id, user.organization_id, new_role
        )

        # Return the new role with org context
        return SetUserRoleResponse(
            user_id=modified_user_id,
            organization_id=user.organization_id,
            role=new_role,
        )

    def bulk_update_member_roles(
        self,
        user: UserToken,
        bulk_input: BulkSetUserRoleInput,
    ) -> BulkSetUserRoleResponse:
        """
        Update multiple members' roles in an organization.

        Updates all roles atomically in a single transaction - either all succeed or all fail.

        Args:
            user: Authenticated user token (for organization context)
            bulk_input: Input containing list of user_id and role pairs

        Returns:
            BulkSetUserRoleResponse with list of updated users

        Raises:
            HTTPException: 400 if input is empty
            HTTPException: 404 if any user not found in organization (via ValueError from repository)
        """
        if not bulk_input.members:
            raise HTTPException(400, "No members provided to update")

        # Prepare role updates as list of tuples
        role_updates = [(member.user_id, member.role) for member in bulk_input.members]

        # Update all roles in a single transaction
        try:
            bulk_update_organization_roles(
                self.session, user.organization_id, role_updates
            )
        except ValueError as e:
            # Repository raises ValueError if any user not found
            raise HTTPException(404, str(e))

        # Build response
        updated_users = [
            SetUserRoleResponse(
                user_id=member.user_id,
                organization_id=user.organization_id,
                role=member.role,
            )
            for member in bulk_input.members
        ]

        return BulkSetUserRoleResponse(updated=updated_users)

    def list_members(
        self,
        user: UserToken,
        page: int = 0,
        per_page: int = 100,
    ) -> ListMembersResponse:
        """
        List all members of an organization.

        Args:
            user: Authenticated user token (for organization context)
            page: Page number (0-indexed)
            per_page: Number of results per page

        Returns:
            ListMembersResponse with members list, pagination info, and total count
        """
        members_data, total_count = list_organization_members(
            self.session, user.organization_id, page=page, per_page=per_page
        )

        # Transform members data to OrganizationMember objects
        members = [
            OrganizationMember(
                user_id=member["user_id"],
                email=member["email"],
                picture=None,  # Not stored in database
                name=member["name"],
                role=member["role"],  # Singular role as enum value
            )
            for member in members_data
        ]

        return ListMembersResponse(
            members=members,
            start=page * per_page,
            limit=per_page,
            total=total_count,
        )
