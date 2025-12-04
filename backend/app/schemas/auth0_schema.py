from database.models_enums import OrgRole
from pydantic import BaseModel, EmailStr, Field


class Invitee(BaseModel):
    email: EmailStr


class Invitation(BaseModel):
    invitee: Invitee
    role: OrgRole = Field(title="Role name")


class CreateInvitationInput(BaseModel):
    invitations: list[Invitation]


class ModifyUserRolesInput(BaseModel):
    roles: list[str] = Field(title="List of Role IDs")


class ModifyUserRolesResponse(BaseModel):
    user_id: str
    added_roles: list[str]
    removed_roles: list[str]
