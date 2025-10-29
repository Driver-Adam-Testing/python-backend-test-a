from pydantic import BaseModel, EmailStr, Field


class Invitee(BaseModel):
    email: EmailStr


class Invitation(BaseModel):
    invitee: Invitee
    roles: list[str] = Field(title="List of Role IDs")


class CreateInvitationInput(BaseModel):
    invitations: list[Invitation]


class ModifyUserRolesInput(BaseModel):
    roles: list[str] = Field(title="List of Role IDs")


class ModifyUserRolesResponse(BaseModel):
    user_id: str
    added_roles: list[str]
    removed_roles: list[str]


class SetUserRoleInput(BaseModel):
    role: str = Field(description="Organization role (e.g., 'super_admin', 'member')")


class SetUserRoleResponse(BaseModel):
    user_id: str
    organization_id: str
    role: str = Field(description="The user's current organization role")


class BulkSetUserRoleItem(BaseModel):
    user_id: str
    role: str = Field(description="Organization role (e.g., 'super_admin', 'member')")


class BulkSetUserRoleInput(BaseModel):
    members: list[BulkSetUserRoleItem]


class BulkSetUserRoleResponse(BaseModel):
    updated: list[SetUserRoleResponse]
