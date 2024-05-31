from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, func, text
from sqlalchemy import DateTime as SaDateTime
from sqlalchemy.dialects.postgresql import UUID as SaUuid
from sqlmodel import Field, Relationship, SQLModel

# Shared properties

# NOTE: SQLModel does not support inheriting table models, just data models. So, we have to repeat the
# created_at and updated_at fields in all models that need them. This is a limitation of SQLModel right now.


# TODO replace email str with EmailStr when sqlmodel supports it
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = None


# Properties to receive via API on creation
class UserCreate(UserBase):  # TODO move these back to API
    password: str


# TODO replace email str with EmailStr when sqlmodel supports it
class UserCreateOpen(SQLModel):
    email: str
    password: str
    full_name: str | None = None


# Properties to receive via API on update, all are optional
# TODO replace email str with EmailStr when sqlmodel supports it
class UserUpdate(UserBase):
    email: str | None = None  # type: ignore
    password: str | None = None


# TODO replace email str with EmailStr when sqlmodel supports it
class UserUpdateMe(SQLModel):
    full_name: str | None = None
    email: str | None = None


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str


class User(UserBase, table=True):  # type: ignore
    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner")
    created_at: datetime | None = Field(
        sa_column=Column(SaDateTime(timezone=True), server_default=func.now()),
        default=None,
    )

    updated_at: datetime | None = Field(
        sa_column=Column(SaDateTime(timezone=True), onupdate=func.now()), default=None
    )


# Properties to return via API, id is always required
class UserOut(UserBase):
    id: UUID


class UsersOut(SQLModel):
    data: list[UserOut]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str
    description: str | None = None


# Properties to receive on item creation
class ItemCreate(ItemBase):
    title: str


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = None  # type: ignore


# Database model, db table inferred from class name
class Item(ItemBase, table=True):  # type: ignore
    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    title: str
    owner_id: UUID | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="items")
    created_at: datetime | None = Field(
        sa_column=Column(SaDateTime(timezone=True), server_default=func.now()),
        default=None,
    )
    updated_at: datetime | None = Field(
        sa_column=Column(SaDateTime(timezone=True), onupdate=func.now()), default=None
    )


# Properties to return via API, id is always required
class ItemOut(ItemBase):
    id: UUID
    owner_id: UUID


class ItemsOut(SQLModel):
    data: list[ItemOut]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: UUID | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str
