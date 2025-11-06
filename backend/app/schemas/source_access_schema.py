"""Schemas for Source Access (ACL) related API requests and responses."""

from typing import Literal
from uuid import UUID

from database.models_enums import OrgRole, PrimaryAssetRole
from pydantic import BaseModel, Field

# ===== Common Types =====
SourceVisibility = Literal["private", "internal", "public"]
SourceUserKind = Literal["user", "team"]
AssignmentType = Literal["direct", "inherited"]


# ===== Team Sources Request Schemas =====
class TeamSourceInput(BaseModel):
    """Input for adding/updating a single source for a team."""

    source_id: str = Field(..., description="Source ID")
    role: PrimaryAssetRole = Field(..., description="Team's role for this source")


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
        description="List of source IDs to remove",
    )


class SourceUserInput(BaseModel):
    """Input for adding/updating a single user for a source."""

    user_id: str = Field(..., description="User ID or Team ID")
    role: PrimaryAssetRole = Field(..., description="Role for this source")


class AddSourceUsersRequest(BaseModel):
    """Request to add users (not teams) to a source."""

    users: list[SourceUserInput] = Field(
        ...,
        min_length=1,
        description="List of users to add",
    )


class UpdateSourceUsersRequest(BaseModel):
    """Request to update source user roles (users only, not teams)."""

    users: list[SourceUserInput] = Field(
        ...,
        min_length=1,
        description="List of users with updated roles",
    )


class RemoveSourceUsersRequest(BaseModel):
    """Request to remove users (not teams) from a source."""

    user_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of user IDs to remove",
    )


# ===== Source Teams Request Schemas =====
class SourceTeamInput(BaseModel):
    """Input for adding/updating a single team for a source."""

    team_id: UUID = Field(..., description="Team ID")
    role: PrimaryAssetRole = Field(..., description="Team's role for this source")


class AddSourceTeamsRequest(BaseModel):
    """Request to add teams to a source."""

    teams: list[SourceTeamInput] = Field(
        ...,
        min_length=1,
        description="List of teams to add",
    )


class UpdateSourceTeamsRequest(BaseModel):
    """Request to update source team roles."""

    teams: list[SourceTeamInput] = Field(
        ...,
        min_length=1,
        description="List of teams with updated roles",
    )


class RemoveSourceTeamsRequest(BaseModel):
    """Request to remove teams from a source."""

    team_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="List of team IDs to remove",
    )


# ===== Team Sources Response Schemas =====
class TeamSourceResponse(BaseModel):
    """Response for a single team source."""

    id: str = Field(..., description="Source ID")
    organization_id: str = Field(..., description="Organization ID")
    kind: str = Field(..., description="Asset type: CODEBASE, FILE, PAGE, etc.")
    display_name: str = Field(..., description="Source display name")
    provider: str | None = Field(None, description="Provider: GITHUB, GITLAB, etc.")
    created_at: str = Field(..., description="ISO datetime when asset was created")
    updated_at: str = Field(..., description="ISO datetime when asset was updated")
    role: PrimaryAssetRole = Field(..., description="Team's role for this source")
    visibility: SourceVisibility = Field(
        ..., description="Source visibility: private, internal, or public"
    )
    team_id: UUID = Field(..., description="Team ID")
    is_browsable: bool = Field(
        ..., description="Whether the source is browsable (has a completed version)"
    )

    class Config:
        from_attributes = True


class TeamSourcesResponse(BaseModel):
    """Response for list of team sources."""

    sources: list[TeamSourceResponse] = Field(..., description="List of team sources")
    total: int = Field(..., description="Total count of team sources")


# ===== Source Teams Response Schemas =====
class SourceTeamResponse(BaseModel):
    """Response for a single team with access to a source."""

    team_id: UUID = Field(..., description="Team ID")
    team_name: str = Field(..., description="Team name")
    role: PrimaryAssetRole = Field(..., description="Team's role for this source")
    member_count: int = Field(..., description="Number of users in the team")
    visibility: SourceVisibility = Field(
        ..., description="Source visibility: private, internal, or public"
    )
    created_at: str = Field(..., description="ISO datetime when access was granted")

    class Config:
        from_attributes = True


class SourceTeamsResponse(BaseModel):
    """Response for list of teams with access to a source."""

    teams: list[SourceTeamResponse] = Field(..., description="List of teams")
    total: int = Field(..., description="Total count of teams")


# ===== Source Users Response Schemas =====
class TeamMembershipInfo(BaseModel):
    """Information about a user's team membership."""

    team_id: UUID = Field(..., description="Team ID")
    display_name: str = Field(..., description="Team name")
    team_role: str = Field(..., description="User's role in the team")
    source_role: PrimaryAssetRole = Field(
        ..., description="Role the team has to the source/asset"
    )

    class Config:
        from_attributes = True


class SourceUserResponse(BaseModel):
    """Response for a single source user with full profile information (users only, not teams)."""

    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str | None = Field(None, description="Email address")
    picture: str | None = Field(None, description="Profile picture URL")
    created_at: str = Field(..., description="ISO datetime when access was granted")
    is_super_admin: bool = Field(
        ..., description="Whether user is a super admin in the organization"
    )
    source_role: PrimaryAssetRole = Field(
        ...,
        description="User's effective role on this source (from direct grant or team grant)",
    )
    assignment_type: AssignmentType = Field(
        ...,
        description="How user has access: 'direct' for direct grants, 'inherited' for team-based access",
    )
    org_role: OrgRole = Field(..., description="User's role in the organization")
    teams: list[TeamMembershipInfo] = Field(
        ...,
        description="List of teams the user belongs to that have access to this source",
    )

    class Config:
        from_attributes = True


class SourceUsersResponse(BaseModel):
    """Response for list of source users (users only, not teams)."""

    users: list[SourceUserResponse] = Field(..., description="List of source users")
    total: int = Field(..., description="Total count of source users")
