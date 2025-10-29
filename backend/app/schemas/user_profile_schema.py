"""Schemas for user profile endpoints."""

from pydantic import BaseModel, Field


class Entitlement(BaseModel):
    """Entitlement model for user profile."""

    name: str = Field(..., description="Entitlement name")
    enabled: bool = Field(..., description="Whether entitlement is enabled")


class MeResponse(BaseModel):
    """Response schema for GET /me endpoint."""

    id: str = Field(..., description="User ID from Auth0")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    organization_id: str = Field(..., description="Organization ID")
    org_role: str = Field(..., description="Organization role (super_admin/member)")
    entitlements: list[Entitlement] | None = Field(
        None, description="List of entitlements or null"
    )
    team_admin: bool = Field(..., description="True if user is admin of ANY team")
    source_admin: bool = Field(
        ...,
        description="True if user has admin role for ANY source (direct grant)",
    )
