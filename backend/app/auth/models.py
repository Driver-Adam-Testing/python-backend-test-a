from pydantic import BaseModel, Field


class User(BaseModel):
    # TODO: remove some redundancy with these aliases
    organization_id: str = Field(..., alias="org_id")
    organization_display_name: str | None = Field("", alias="org_name")
    organization_name: str | None = Field("", alias="org_name")
    user_id: str = Field(..., alias="sub")
    issuer: str = Field(..., alias="iss")
    subject: str = Field(..., alias="sub")
    audience: list[str] | str = Field(..., alias="aud")
    issued_at: int = Field(..., alias="iat")
    expiration: int = Field(..., alias="exp")
    scope: str = Field("", alias="scope")
    authorized_party: str = Field("", alias="azp")
    permissions: list[str] = Field(default_factory=list)
    email: str | None = Field("", alias="user_email")
    full_name: str | None = Field("", alias="user_full_name")


class M2M(BaseModel):
    issuer: str = Field(..., alias="iss")
    subject: str = Field(..., alias="sub")
    audience: list[str] | str = Field(..., alias="aud")
    issued_at: int = Field(..., alias="iat")
    expiration: int = Field(..., alias="exp")
    authorized_party: str = Field("", alias="azp")
