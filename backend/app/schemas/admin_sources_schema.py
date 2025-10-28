"""Schemas for Admin Sources API requests and responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ===== Common Types =====
SourceVisibility = Literal["private", "internal", "public"]


# ===== Admin Sources Request =====
class AdminSourcesRequest(BaseModel):
    """Request parameters for admin sources list."""

    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    search: str | None = Field(None, description="Search by display name")
    kind: list[str] | None = Field(None, description="Filter by asset type")
    top_language: list[str] | None = Field(None, description="Filter by language")
    tag_ids: list[str] | None = Field(None, description="Filter by tag IDs")
    sort_by: str = Field(default="updated_at", description="Sort field")
    sort_direction: Literal["ASC", "DESC"] = Field(
        default="DESC", description="Sort direction"
    )


# ===== Admin Sources Response =====
class AdminSourceRecord(BaseModel):
    """Individual source record with admin metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Primary asset ID")
    organization_id: str = Field(..., description="Organization ID")
    kind: str = Field(..., description="Asset type")
    display_name: str = Field(..., description="Source display name")
    provider: str | None = Field(None, description="Provider type")
    created_at: str = Field(..., description="ISO datetime when created")
    updated_at: str = Field(..., description="ISO datetime when updated")
    visibility: SourceVisibility = Field(..., description="Source visibility")
    members_count: int = Field(..., description="Count of user grants")
    teams_count: int = Field(..., description="Count of team grants")
    tags: list[dict] | None = Field(None, description="Associated tags")


class AdminSourcesResponse(BaseModel):
    """Response for admin sources list."""

    results: list[AdminSourceRecord] = Field(..., description="List of sources")
    total_count: int = Field(..., description="Total count of sources")
