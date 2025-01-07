from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy
from database.models_v2_enums import NodeKind, PrimaryAssetKind, VersionStatus
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SaUuid
from sqlmodel import Field, Relationship, SQLModel, text


class PrimaryAsset(SQLModel, table=True):  # type: ignore
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
    repository_id: str | None
    organization_id: str
    kind: PrimaryAssetKind

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
    versions: list["Version"] = Relationship(back_populates="primary_asset")

    tags: list["Tag"] = Relationship(  # noqa: F821
        back_populates="primary_assets",
        sa_relationship_kwargs={"secondary": "v2_primary_asset_tag"},
    )


class Version(SQLModel, table=True):  # type: ignore
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

    status: VersionStatus

    previous_version_id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            ForeignKey("v2_version.id", ondelete="SET NULL"),
            nullable=True,
        ),
        default=None,
    )

    primary_asset: "PrimaryAsset" = Relationship(back_populates="versions")
    nodes: list["Node"] = Relationship(back_populates="version")
    root_node: Optional["Node"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(Version.id == Node.version_id)",
            "order_by": "func.length(Node.relative_path)",
            "uselist": False,
        }
    )


# TODO: consider kind on Node. Maybe a bool or enum?
class Node(SQLModel, table=True):  # type: ignore
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
    kind: NodeKind
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
    # TODO: enforce data structure with field_validator when misc_metadata is populated
    misc_metadata: dict | None = Field(  # type: ignore
        sa_column=Column(JSONB, nullable=True), default=None
    )

    version: "Version" = Relationship(back_populates="nodes")
    contents: list["DerivedContent"] = Relationship(back_populates="node")  # noqa: F821

    parent_node: Optional["Node"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(Node.version_id == foreign(Node.version_id), Node.version_id == remote(Node.version_id), Node.relative_path != remote(Node.relative_path), Node.relative_path.like(remote(Node.relative_path) + '%'))",
            "uselist": False,
            "viewonly": True,
            "lazy": "select",
            "remote_side": "[Node.version_id]",
            "order_by": "desc(func.length(Node.relative_path))",
        }
    )
    document_sources: list["DocumentSource"] = Relationship(  # noqa: F821
        back_populates="source_node",
        sa_relationship_kwargs={"foreign_keys": "DocumentSource.source_node_id"},
    )
    page_sources: list["DocumentSource"] = Relationship(  # noqa: F821
        back_populates="page_node",
        sa_relationship_kwargs={"foreign_keys": "DocumentSource.page_node_id"},
    )


class PrimaryAssetTag(SQLModel, table=True):
    __tablename__ = "v2_primary_asset_tag"
    tag_id: UUID = Field(default=None, primary_key=True, foreign_key="tags.id")
    primary_asset_id: UUID = Field(
        default=None, primary_key=True, foreign_key="v2_primary_asset.id"
    )
