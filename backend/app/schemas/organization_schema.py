"""Schemas for organization-related API responses."""

from pydantic import BaseModel, Field


class OrganizationMember(BaseModel):
    """Organization member with user details and role."""

    user_id: str = Field(description="Auth0 user ID")
    email: str | None = Field(description="User email address")
    picture: str | None = Field(
        default=None, description="User profile picture URL (not stored in DB)"
    )
    name: str | None = Field(description="User display name")
    role: str = Field(description="Organization role (e.g., 'super_admin', 'member')")


class ListMembersResponse(BaseModel):
    """Response for listing organization members with pagination."""

    members: list[OrganizationMember] = Field(description="List of organization members")
    start: int = Field(description="Pagination offset (page * per_page)")
    limit: int = Field(description="Number of items per page")
    total: int = Field(description="Total number of members in organization")
