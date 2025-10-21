"""Schemas for Team Member-related API requests and responses."""

from typing import Literal

from pydantic import BaseModel, Field


# ===== Request Schemas =====
class TeamMemberAddInput(BaseModel):
    """Input for adding a single team member."""

    userId: str = Field(..., description="User ID")
    role: Literal["admin", "member"] = Field(..., description="Team role")


class AddTeamMembersRequest(BaseModel):
    """Request to add members to a team."""

    members: list[TeamMemberAddInput] = Field(
        ...,
        min_length=1,
        description="List of members to add",
    )


class UpdateTeamMembersRequest(BaseModel):
    """Request to update team member roles."""

    members: list[TeamMemberAddInput] = Field(
        ...,
        min_length=1,
        description="List of members with updated roles",
    )


class RemoveTeamMembersRequest(BaseModel):
    """Request to remove members from a team."""

    userIds: list[str] = Field(
        ...,
        min_length=1,
        description="List of user IDs to remove",
    )


# ===== Response Schemas =====
class TeamMemberResponse(BaseModel):
    """Response for a single team member."""

    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    picture: str = Field(..., description="User's profile picture URL")
    team_id: str = Field(..., description="Team ID")
    team_name: str = Field(..., description="Team name")
    team_role: Literal["admin", "member"] = Field(..., description="Team role")
    created_at: str = Field(..., description="ISO datetime when member was added")
    last_active: str = Field(..., description="ISO datetime of last activity")

    class Config:
        from_attributes = True


class TeamMembersResponse(BaseModel):
    """Response for list of team members."""

    members: list[TeamMemberResponse] = Field(..., description="List of team members")
    total: int = Field(..., description="Total count of team members")
