"""Schemas for Source Access (ACL) related API requests and responses."""

from typing import Literal

from pydantic import BaseModel, Field

# ===== Common Types =====
SourceRole = Literal["admin", "member"]
SourceVisibility = Literal["private", "internal", "public"]
SourceMemberKind = Literal["user", "team"]


# ===== Team Sources Request Schemas =====
class TeamSourceInput(BaseModel):
    """Input for adding/updating a single source for a team."""

    source_id: str = Field(..., description="Primary asset ID (source ID)")
    role: SourceRole = Field(..., description="Source role")


class AddTeamSourcesRequest(BaseModel):
    """Request to add sources to a team."""

    sources: list[TeamSourceInput] = Field(
        ...,
        min_length=1,
        description="List of sources to add",
    )


class UpdateTeamSourcesRequest(BaseModel):
    """Request to update team source roles."""

    sources: list[TeamSourceInput] = Field(
        ...,
        min_length=1,
        description="List of sources with updated roles",
    )


class RemoveTeamSourcesRequest(BaseModel):
    """Request to remove sources from a team."""

    source_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of source IDs (primary_asset_id) to remove",
    )


# ===== Source Members Request Schemas =====
class SourceMemberInput(BaseModel):
    """Input for adding/updating a single member for a source."""

    member_id: str = Field(..., description="User ID or Team ID")
    kind: SourceMemberKind = Field(..., description="Member type: user or team")
    role: SourceRole = Field(..., description="Source role")


class AddSourceMembersRequest(BaseModel):
    """Request to add members to a source."""

    members: list[SourceMemberInput] = Field(
        ...,
        min_length=1,
        description="List of members (users or teams) to add",
    )


class UpdateSourceMembersRequest(BaseModel):
    """Request to update source member roles."""

    members: list[SourceMemberInput] = Field(
        ...,
        min_length=1,
        description="List of members with updated roles",
    )


class RemoveSourceMemberInput(BaseModel):
    """Input for removing a single member from a source."""

    member_id: str = Field(..., description="User ID or Team ID")
    kind: SourceMemberKind = Field(..., description="Member type: user or team")


class RemoveSourceMembersRequest(BaseModel):
    """Request to remove members from a source."""

    members: list[RemoveSourceMemberInput] = Field(
        ...,
        min_length=1,
        description="List of members to remove",
    )


# ===== Team Sources Response Schemas =====
class TeamSourceResponse(BaseModel):
    """Response for a single team source."""

    id: str = Field(..., description="Primary asset ID")
    organization_id: str = Field(..., description="Organization ID")
    kind: str = Field(..., description="Asset type: CODEBASE, FILE, PAGE, etc.")
    display_name: str = Field(..., description="Source display name")
    provider: str | None = Field(None, description="Provider: GITHUB, GITLAB, etc.")
    created_at: str = Field(..., description="ISO datetime when asset was created")
    updated_at: str = Field(..., description="ISO datetime when asset was updated")
    role: SourceRole = Field(..., description="Team's role for this source")
    visibility: SourceVisibility = Field(
        ..., description="Visibility: private, internal, or public"
    )
    team_id: str = Field(..., description="Team ID")

    class Config:
        from_attributes = True


class TeamSourcesResponse(BaseModel):
    """Response for list of team sources."""

    sources: list[TeamSourceResponse] = Field(..., description="List of team sources")
    total: int = Field(..., description="Total count of team sources")


# ===== Source Members Response Schemas =====
class SourceMemberResponse(BaseModel):
    """Response for a single source member (user or team)."""

    member_id: str = Field(..., description="User ID or Team ID")
    kind: SourceMemberKind = Field(..., description="Member type: user or team")
    name: str = Field(..., description="User name or team name")
    email: str | None = Field(
        None, description="Email (for users only, null for teams)"
    )
    picture: str | None = Field(
        None, description="Profile picture (for users only, null for teams)"
    )
    source_id: str = Field(..., description="Source (primary asset) ID")
    source_name: str = Field(..., description="Source display name")
    source_role: SourceRole = Field(..., description="Member's role for this source")
    visibility: SourceVisibility = Field(
        ..., description="Visibility: private, internal, or public"
    )
    created_at: str = Field(..., description="ISO datetime when access was granted")

    class Config:
        from_attributes = True


class SourceMembersResponse(BaseModel):
    """Response for list of source members."""

    members: list[SourceMemberResponse] = Field(
        ..., description="List of source members"
    )
    total: int = Field(..., description="Total count of source members")
