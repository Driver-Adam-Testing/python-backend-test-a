import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, func
from sqlmodel import CheckConstraint, Column, Field, Index, Relationship, SQLModel

from ..models_enums import PrimaryAssetRole, PrincipalKind

if TYPE_CHECKING:
    from .base import PrimaryAsset


class PrimaryAssetRoleGrant(SQLModel, table=True):
    __tablename__ = "primary_asset_role_grant"
    __table_args__ = (
        CheckConstraint(
            """
            (principal_kind = 'user'   AND user_id IS NOT NULL AND team_id IS NULL) OR
            (principal_kind = 'team'   AND team_id IS NOT NULL AND user_id IS NULL) OR
            (principal_kind = 'org'    AND user_id IS NULL    AND team_id IS NULL) OR
            (principal_kind = 'public' AND user_id IS NULL    AND team_id IS NULL)
            """,
            name="chk_exactly_one_principal",
        ),
        CheckConstraint(
            "principal_kind NOT IN ('org','public') OR role = 'asset_member'",
            name="chk_org_public_view_only",
        ),
        # One public grant per asset
        Index(
            "uq_parg_public",
            "primary_asset_id",
            unique=True,
            postgresql_where=(Column("principal_kind") == "public"),
        ),
        # One user grant per asset
        Index(
            "uq_parg_user",
            "primary_asset_id",
            "user_id",
            unique=True,
            postgresql_where=(Column("user_id").isnot(None)),
        ),
        # One team grant per asset
        Index(
            "uq_parg_team",
            "primary_asset_id",
            "team_id",
            unique=True,
            postgresql_where=(Column("team_id").isnot(None)),
        ),
        # One org-wide grant per asset
        Index(
            "uq_parg_orgwide",
            "primary_asset_id",
            unique=True,
            postgresql_where=(Column("principal_kind") == "org"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    primary_asset_id: uuid.UUID = Field(foreign_key="primary_asset.id", index=True)
    organization_id: str = Field(
        foreign_key="organization.id", index=True
    )  # TODO: is this duplicative? Can it be removed?
    principal_kind: PrincipalKind
    user_id: str | None = Field(default=None, foreign_key="user.id", index=True)
    team_id: uuid.UUID | None = Field(default=None, foreign_key="team.id", index=True)
    role: PrimaryAssetRole
    # created_by: uuid.UUID = Field(foreign_key="user.id") # TODO: want this for audit logging
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    primary_asset: "PrimaryAsset" = Relationship(back_populates="grants")
