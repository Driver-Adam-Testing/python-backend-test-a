"""Schemas for organization-related API responses."""

from database.models_enums import OrgRole
from pydantic import BaseModel, Field


class OrganizationMember(BaseModel):
    """Organization member with user details and role."""

    user_id: str = Field(description="Auth0 user ID")
    email: str | None = Field(description="User email address")
    picture: str | None = Field(
        default=None, description="User profile picture URL (not stored in DB)"
    )
    name: str | None = Field(description="User display name")
    role: OrgRole = Field(description="Organization role enum")
    has_source_access: bool = Field(
        default=False,
        description="Whether user has direct access to the source (only populated when source_id query param is provided)",
    )
    has_team_access: bool = Field(
        default=False,
        description="Whether user is a member of the team (only populated when team_id query param is provided)",
    )


class ListMembersResponse(BaseModel):
    """Response for listing organization members with pagination."""

    members: list[OrganizationMember] = Field(
        description="List of organization members"
    )
    offset: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum number of items returned")
    total: int = Field(description="Total number of members in organization")


class SetUserRoleInput(BaseModel):
    """Input for setting a user's organization role."""

    role: OrgRole = Field(description="Organization role enum")


class SetUserRoleResponse(BaseModel):
    """Response for setting a user's organization role."""

    user_id: str = Field(description="Auth0 user ID")
    organization_id: str = Field(description="Organization ID")
    role: OrgRole = Field(description="The user's current organization role")


class BulkSetUserRoleItem(BaseModel):
    """Item for bulk setting user roles."""

    user_id: str = Field(description="Auth0 user ID")
    role: OrgRole = Field(description="Organization role enum")


class BulkSetUserRoleInput(BaseModel):
    """Input for bulk setting user roles."""

    members: list[BulkSetUserRoleItem] = Field(description="List of user role updates")


class BulkSetUserRoleResponse(BaseModel):
    """Response for bulk setting user roles."""

    updated: list[SetUserRoleResponse] = Field(
        description="List of successfully updated users"
    )
