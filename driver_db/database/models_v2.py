from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

import sqlalchemy
from pydantic import field_validator
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as SaUuid
from sqlmodel import Field, Relationship, Session, SQLModel, select, text


class PrimaryAssetTypeEnum(str, Enum):
    CODEBASE = "CODEBASE"
    FILE = "FILE"
    PAGE = "PAGE"
    PAGE_TEMPLATE = "PAGE_TEMPLATE"


class PrimaryAssetRow(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_primary_asset"
    __table_args__ = (
        Index(
            "ix_v2_primary_asset_organization_id_display_name",
            "organization_id",
            "display_name",
            unique=True,
        ),
    )

    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    display_name: str
    organization_id: str
    primary_asset_type: str
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    updated_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        default=None,
    )
    versions: list["VersionRow"] = Relationship(back_populates="primary_asset")
    tags: list["Tag"] = Relationship(  # noqa: F821
        back_populates="primary_assets",
        sa_relationship_kwargs={"secondary": "v2_primary_asset_tag"},
    )

    @field_validator("primary_asset_type", mode="before")
    def validate_primary_asset_type(cls, value: str) -> str:
        if value not in PrimaryAssetTypeEnum:
            raise ValueError(
                f"primary_asset_type must be one of {list(PrimaryAssetTypeEnum)}"
            )
        return value


class VersionRow(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_version"
    __table_args__ = (
        Index(
            "ix_v2_version_primary_asset_id_display_name",
            "primary_asset_id",
            "display_name",
            unique=True,
        ),
    )

    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    primary_asset_id: UUID = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            ForeignKey("v2_primary_asset.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    display_name: str
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    updated_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        default=None,
    )

    primary_asset: "PrimaryAssetRow" = Relationship(back_populates="versions")
    nodes: list["NodeRow"] = Relationship(back_populates="version")
    root_node: Optional["NodeRow"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(VersionRow.id == NodeRow.version_id)",
            "order_by": "func.length(NodeRow.relative_path)",
            "uselist": False,
        }
    )


class NodeRow(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_node"
    __table_args__ = (
        Index(
            "ix_version_id_relative_path", "version_id", "relative_path", unique=True
        ),
    )

    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    version_id: UUID = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            ForeignKey("v2_version.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    relative_path: str = Field(
        sa_column=Column(sqlalchemy.Text, nullable=False, index=True)
    )
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    updated_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        default=None,
    )

    version: "VersionRow" = Relationship(back_populates="nodes")
    contents: list["DerivedContent"] = Relationship(back_populates="node")  # noqa: F821

    parent_node: Optional["NodeRow"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(NodeRow.version_id == foreign(NodeRow.version_id), NodeRow.version_id == remote(NodeRow.version_id), NodeRow.relative_path != remote(NodeRow.relative_path), NodeRow.relative_path.like(remote(NodeRow.relative_path) + '%'))",
            "uselist": False,
            "viewonly": True,
            "lazy": "select",
            "remote_side": "[NodeRow.version_id]",
            "order_by": "desc(func.length(NodeRow.relative_path))",
        }
    )
    # child_nodes: list["NodeRow"] = Relationship(
    #     sa_relationship_kwargs={
    #         "primaryjoin": "and_(NodeRow.version_id == foreign(NodeRow.version_id), NodeRow.version_id == remote(NodeRow.version_id), NodeRow.relative_path != remote(NodeRow.relative_path), remote(NodeRow.relative_path).like(NodeRow.relative_path + '%'))",
    #         "viewonly": True,
    #         "lazy": "select",
    #         "remote_side": "[NodeRow.version_id]",
    #         "order_by": "asc(func.length(NodeRow.relative_path))"
    #     }
    # )


class FullNodeView(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_full_node"
    primary_asset_id: UUID | None = Field(default=None, primary_key=True)
    primary_asset_display_name: str | None = Field(default=None)
    primary_asset_organization_id: str | None = Field(default=None)
    primary_asset_created_at: None | datetime = Field(default=None)
    primary_asset_updated_at: None | datetime = Field(default=None)
    primary_asset_primary_asset_type: str | None = Field(default=None)
    version_id: UUID | None = Field(default=None, primary_key=True)
    version_display_name: str | None = Field(default=None)
    version_created_at: None | datetime = Field(default=None)
    version_updated_at: None | datetime = Field(default=None)
    node_id: UUID | None = Field(primary_key=True)
    node_relative_path: str | None = Field(default=None)
    node_created_at: None | datetime = Field(default=None)
    node_updated_at: None | datetime = Field(default=None)

    def add(self, session: Session) -> None:
        if self.primary_asset_id:
            primary_asset = session.exec(
                select(PrimaryAssetRow).where(
                    PrimaryAssetRow.id == self.primary_asset_id
                )
            ).one_or_none()
            if primary_asset:
                primary_asset.display_name = self.primary_asset_display_name
                primary_asset.organization_id = self.primary_asset_organization_id
            else:
                primary_asset = PrimaryAssetRow(
                    id=self.primary_asset_id,
                    display_name=self.primary_asset_display_name,
                    organization_id=self.primary_asset_organization_id,
                )
                session.add(primary_asset)

        if self.version_id:
            version = session.exec(
                select(VersionRow).where(VersionRow.id == self.version_id)
            ).one_or_none()
            if version:
                version.display_name = self.version_display_name
            else:
                version = VersionRow(
                    id=self.version_id,
                    display_name=self.version_display_name,
                )
                session.add(version)

        if self.node_id:
            node = session.exec(
                select(NodeRow).where(NodeRow.id == self.node_id)
            ).one_or_none()
            if node:
                node.relative_path = self.node_relative_path
            else:
                node = NodeRow(
                    id=self.node_id,
                    relative_path=self.node_relative_path,
                )
                session.add(node)


class PrimaryAssetTag(SQLModel, table=True):
    __tablename__ = "v2_primary_asset_tag"
    tag_id: UUID = Field(default=None, primary_key=True, foreign_key="tags.id")
    primary_asset_id: UUID = Field(
        default=None, primary_key=True, foreign_key="v2_primary_asset.id"
    )
