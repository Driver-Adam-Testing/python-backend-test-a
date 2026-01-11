"""Schemas for Team-related API requests and responses."""

from database.models_enums import TeamRole
from pydantic import BaseModel, Field


# ===== Team Member Input =====
class TeamMemberInput(BaseModel):
    """Input for adding a team member."""

    user_id: str = Field(..., description="User ID")
    role: TeamRole = Field(..., description="Team role")


# ===== Team Requests =====
class CreateTeamRequest(BaseModel):
    """Request to create a new team."""

    name: str = Field(..., min_length=1, max_length=255, description="Team name")
    members: list[TeamMemberInput] | None = Field(
        default=None,
        description="Optional list of initial team members",
    )


class UpdateTeamRequest(BaseModel):
    """Request to update a team."""

    name: str = Field(..., min_length=1, max_length=255, description="New team name")


class SearchTeamsRequest(BaseModel):
    """Request to search teams."""

    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=30, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


# ===== Team Responses =====
class TeamResponse(BaseModel):
    """Response for a single team."""

    id: str = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    admins: int = Field(..., description="Count of team admins")
    members: int = Field(..., description="Count of team members")
    sources: int = Field(..., description="Count of sources accessible to team")
    created_at: str = Field(..., description="ISO datetime when created")
    updated_at: str = Field(..., description="ISO datetime when last updated")
    has_user_access: bool = Field(
        default=False,
        description="Whether the specified user is a member of this team (only populated when user_id query param is provided)",
    )
    has_source_access: bool = Field(
        default=False,
        description="Whether this team has access to the specified source (only populated when source_id query param is provided)",
    )

    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    """Response for team detail endpoint with user's effective role."""

    effective_team_role: TeamRole = Field(
        ...,
        description="Current user's effective role in this team (team_admin for super admins)",
    )


class TeamsResponse(BaseModel):
    """Response for list of teams."""

    teams: list[TeamResponse] = Field(..., description="List of teams")
    total: int = Field(..., description="Total count of teams")


# ===== Pagination Parameters =====
class TeamsPaginationParams(BaseModel):
    """Pagination parameters for teams list."""

    limit: int = Field(default=30, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    search: str | None = Field(
        default=None, description="Optional search query to filter teams by name"
    )
