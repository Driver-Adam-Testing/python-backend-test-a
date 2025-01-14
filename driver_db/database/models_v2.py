import hashlib
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from database.models_v2_enums import NodeKind, PrimaryAssetKind, VersionStatus
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


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

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
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
    versions: list["Version"] = Relationship(
        back_populates="primary_asset",
        sa_relationship_kwargs={
            "passive_deletes": True,
            "cascade": "all, delete-orphan",
        },
    )
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

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    primary_asset_id: UUID = Field(
        foreign_key="v2_primary_asset.id",
        nullable=False,
        ondelete="CASCADE",
    )
    display_name: str
    status: VersionStatus
    previous_version_id: UUID | None = Field(
        default=None,
        nullable=True,
        foreign_key="v2_version.id",
        ondelete="SET NULL",
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
    primary_asset: "PrimaryAsset" = Relationship(back_populates="versions")
    nodes: list["Node"] = Relationship(
        back_populates="version",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )
    root_node: Optional["Node"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(Version.id == Node.version_id)",
            "order_by": "func.length(Node.relative_path)",
            "uselist": False,
        }
    )


class Node(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_node"
    __table_args__ = (
        Index(
            "ix_version_id_relative_path", "version_id", "relative_path", unique=True
        ),
    )
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    kind: NodeKind
    version_id: UUID = Field(
        foreign_key="v2_version.id",
        ondelete="CASCADE",
        nullable=False,
    )
    relative_path: str = Field(nullable=False, index=True)

    # TODO: enforce data structure with field_validator when misc_metadata is populated
    misc_metadata: dict | None = Field(  # type: ignore
        sa_column=Column(JSONB, nullable=True), default=None
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
    version: "Version" = Relationship(back_populates="nodes")
    contents: list["DerivedContent"] = Relationship(  # noqa: F821
        back_populates="node",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )

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

    @property
    def s3_url(self) -> str:
        org_id_hash = hashlib.sha256(
            self.version.primary_asset.organization_id.encode()
        ).hexdigest()[:63]
        return f"https://{org_id_hash}.s3.amazonaws.com/{self.version.primary_asset_id}/{self.version_id}/{self.relative_path}"


class PrimaryAssetTag(SQLModel, table=True):
    __tablename__ = "v2_primary_asset_tag"
    tag_id: UUID = Field(primary_key=True, ondelete="CASCADE", foreign_key="tags.id")
    primary_asset_id: UUID = Field(
        primary_key=True, ondelete="CASCADE", foreign_key="v2_primary_asset.id"
    )
