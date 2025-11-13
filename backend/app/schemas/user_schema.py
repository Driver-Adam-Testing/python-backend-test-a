"""Schemas for User-related API requests and responses."""

from enum import Enum

from database.models_enums import OrgRole, PrimaryAssetRole, TeamRole
from pydantic import BaseModel, Field


class AssignmentType(str, Enum):
    DIRECT = "direct"
    INHERITED = "inherited"


# ===== User Search =====
class SearchUsersRequest(BaseModel):
    """Request to search organization users."""

    query: str = Field(..., min_length=1, description="Search query for name or email")
    limit: int = Field(default=30, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class UserResponse(BaseModel):
    """Response for a single user."""

    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    picture: str = Field(..., description="User's profile picture URL")

    class Config:
        from_attributes = True


class OrganizationMembersResponse(BaseModel):
    """Response for list of organization users."""

    members: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total count of users")


# ===== User Teams Request Schemas =====
class UserTeamInput(BaseModel):
    """Input for adding/updating a single team for a user."""

    team_id: str = Field(..., description="Team ID")
    role: TeamRole = Field(..., description="Team role: team_admin or team_member")


class AddUserTeamsRequest(BaseModel):
    """Request to add user to teams."""

    teams: list[UserTeamInput] = Field(
        ...,
        min_length=1,
        description="List of teams to add user to",
    )


class UpdateUserTeamsRequest(BaseModel):
    """Request to update user's team roles."""

    teams: list[UserTeamInput] = Field(
        ...,
        min_length=1,
        description="List of teams with updated roles",
    )


class RemoveUserTeamsRequest(BaseModel):
    """Request to remove user from teams."""

    team_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of team IDs to remove user from",
    )


# ===== User Teams Response Schemas =====
class UserTeamResponse(BaseModel):
    """Response for a single user team."""

    id: str = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    admins: int = Field(..., description="Count of team admins")
    members: int = Field(..., description="Count of team members")
    sources: int = Field(..., description="Count of sources accessible to team")
    created_at: str = Field(..., description="ISO datetime when created")
    updated_at: str = Field(..., description="ISO datetime when last updated")
    role: TeamRole = Field(..., description="User's role in this team")

    class Config:
        from_attributes = True


class UserTeamsResponse(BaseModel):
    """Response for list of user's teams."""

    teams: list[UserTeamResponse] = Field(..., description="List of user's teams")
    total: int = Field(..., description="Total count of user's teams")


# ===== User Sources Request Schemas =====
class UserSourceInput(BaseModel):
    """Input for adding/updating a single source for a user."""

    source_id: str = Field(..., description="Primary asset ID (source ID)")
    role: PrimaryAssetRole = Field(
        ..., description="Source role: asset_admin or asset_member"
    )


class AddUserSourcesRequest(BaseModel):
    """Request to grant user direct access to sources."""

    sources: list[UserSourceInput] = Field(
        ...,
        min_length=1,
        description="List of sources to grant access to",
    )


class UpdateUserSourcesRequest(BaseModel):
    """Request to update user's source roles."""

    sources: list[UserSourceInput] = Field(
        ...,
        min_length=1,
        description="List of sources with updated roles",
    )


class RemoveUserSourcesRequest(BaseModel):
    """Request to remove user's direct access to sources."""

    source_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of source IDs (primary_asset_id) to remove",
    )


# ===== User Sources Response Schemas =====
class UserSourceTeamInfo(BaseModel):
    team_id: str = Field(..., description="Team ID")
    display_name: str = Field(..., description="Team display name")
    team_role: TeamRole = Field(..., description="User's role in this team")
    source_role: PrimaryAssetRole = Field(..., description="Team's role on this asset")


class UserSourceResponse(BaseModel):
    """Response for a single user source."""

    id: str = Field(..., description="Primary asset ID")
    organization_id: str = Field(..., description="Organization ID")
    kind: str = Field(..., description="Asset type: CODEBASE, FILE, PAGE, etc.")
    display_name: str = Field(..., description="Source display name")
    provider: str | None = Field(None, description="Provider: GITHUB, GITLAB, etc.")
    created_at: str = Field(..., description="ISO datetime when asset was created")
    updated_at: str = Field(..., description="ISO datetime when asset was updated")
    effective_role: PrimaryAssetRole = Field(
        ..., description="User's effective role for this source (highest priority)"
    )
    source_role: PrimaryAssetRole | None = Field(
        None, description="Role directly granted to the user on this asset"
    )
    asset_org_role: PrimaryAssetRole | None = Field(
        None, description="Role granted via org-level grant on this asset"
    )
    user_org_role: OrgRole = Field(..., description="User's organization role")
    is_super_admin: bool = Field(
        ..., description="Whether user is a super admin in the organization"
    )
    assignment_type: AssignmentType = Field(
        ...,
        description="Whether the effective role is 'direct' (from user grant) or 'inherited' (from org/team/super admin)",
    )
    teams: list[UserSourceTeamInfo] = Field(
        default_factory=list,
        description="Teams the user is on that have grants to this asset",
    )
    user_id: str = Field(..., description="User ID")
    is_browsable: bool = Field(
        ..., description="Whether the source is browsable (has a completed version)"
    )

    class Config:
        from_attributes = True


class UserSourcesResponse(BaseModel):
    """Response for list of user's sources."""

    sources: list[UserSourceResponse] = Field(..., description="List of user sources")
    total: int = Field(..., description="Total count of user sources")


# ===== Generic Message Response =====
class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")
