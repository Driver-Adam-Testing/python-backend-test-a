"""Schemas for RBAC Member Search API requests and responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ===== Common Types =====
MemberKind = Literal["user", "team"]


# ===== Member Search Request =====
class SearchMembersRequest(BaseModel):
    """Request to search for members (users and teams)."""

    query: str = Field(..., min_length=1, description="Search query for name or email")
    limit: int = Field(default=30, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


# ===== Member Search Response =====
class MemberSearchItem(BaseModel):
    """Individual member search result (user or team)."""

    model_config = ConfigDict(from_attributes=True)

    member_id: str = Field(..., description="Member ID (user_id or team_id)")
    kind: MemberKind = Field(..., description="Member type: user or team")
    name: str = Field(..., description="Member name")
    email: str | None = Field(None, description="Email address (users only)")
    picture: str | None = Field(None, description="Profile picture URL (users only)")


class MemberSearchResponse(BaseModel):
    """Response for member search."""

    items: list[MemberSearchItem] = Field(..., description="List of matching members")
    total: int = Field(..., description="Total count of matching members")
