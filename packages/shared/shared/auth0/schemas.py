from typing import Any

from pydantic import BaseModel, EmailStr, Field


class Invitee(BaseModel):
    email: EmailStr


class Invitation(BaseModel):
    invitee: Invitee
    roles: list[str] = Field(title="List of Role IDs")
    app_metadata: dict[str, Any] | None = None
    user_metadata: dict[str, Any] | None = None


class CreateInvitationInput(BaseModel):
    invitations: list[Invitation]


class ModifyUserRolesInput(BaseModel):
    roles: list[str] = Field(title="List of Role IDs")


class ModifyUserRolesResponse(BaseModel):
    user_id: str
    added_roles: list[str]
    removed_roles: list[str]
