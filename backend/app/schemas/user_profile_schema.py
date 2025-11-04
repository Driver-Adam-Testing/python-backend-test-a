"""Schemas for user profile endpoints."""

from pydantic import BaseModel, Field


class MeResponse(BaseModel):
    """Response schema for GET /me endpoint."""

    id: str = Field(..., description="User ID from Auth0")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    organization_id: str = Field(..., description="Organization ID")
    org_role: str = Field(..., description="Organization role (super_admin/member)")
    entitlements: None = Field(None, description="List of entitlements or null")
    team_admin: bool = Field(..., description="True if user is admin of ANY team")
    source_admin: bool = Field(
        ...,
        description="True if user has effective admin role on ANY asset",
    )
