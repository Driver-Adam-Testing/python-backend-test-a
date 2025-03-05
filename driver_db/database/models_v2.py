import hashlib
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from database.models_v2_enums import NodeKind, PrimaryAssetKind, VersionStatus
from sqlalchemy import Column, DateTime, Index, func
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
    display_name: str = Field(index=True)
    repository_id: str | None
    organization_id: str = Field(index=True)
    kind: PrimaryAssetKind = Field(index=True)
    installation_id: UUID | None = Field(
        foreign_key="git_provider_app_installations.id",
        nullable=True,
        ondelete="SET NULL",
        default=None,
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
    related_content_last_updated: None | datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True),
        default=None,
    )
    versions: list["Version"] = Relationship(
        back_populates="primary_asset",
        sa_relationship_kwargs={
            "passive_deletes": True,
            "cascade": "all, delete-orphan",
            "order_by": "desc(Version.updated_at)",
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
        index=True,
    )
    creator_id: str = Field(
        foreign_key="user_cache.id",
        nullable=True,
        ondelete="SET NULL",
    )
    display_name: str
    status: VersionStatus = Field(index=True)
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
            index=True,
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
    creator: "UserCache" = Relationship(back_populates="created_versions")
    root_node: Optional["Node"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(Version.id == Node.version_id)",
            "order_by": "func.length(Node.relative_path)",
            "uselist": False,
            "viewonly": True,
        }
    )
    inspector_runs: list["InspectorRun"] = Relationship(  # noqa: F821
        back_populates="version",
        passive_deletes="all",
        sa_relationship_kwargs={
            "order_by": "desc(InspectorRun.updated_at)",
        },
    )


class Node(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_node"
    __table_args__ = (
        Index(
            "ix_version_id_relative_path", "version_id", "relative_path", unique=True
        ),
        # Index for root_node on a version
        Index(
            "idx_node_version_id_relative_path_length",
            "version_id",
            func.length("relative_path"),
        ),
        # Index for node ancestor searching
        Index(
            "ix_node_version_id_relative_path_pattern_ops",
            "version_id",
            postgresql_ops={"relative_path": "text_pattern_ops"},
        ),
    )
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    kind: NodeKind
    version_id: UUID = Field(
        foreign_key="v2_version.id",
        ondelete="CASCADE",
        nullable=False,
        index=True,
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
        sa_relationship_kwargs={
            "foreign_keys": "DocumentSource.source_node_id",
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )
    page_sources: list["DocumentSource"] = Relationship(  # noqa: F821
        back_populates="page_node",
        sa_relationship_kwargs={
            "foreign_keys": "DocumentSource.page_node_id",
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )

    @property
    def s3_url(self) -> str:
        org_id_hash = hashlib.sha256(
            self.version.primary_asset.organization_id.encode()
        ).hexdigest()[:63]
        return f"https://{org_id_hash}.s3.amazonaws.com/{self.version.primary_asset_id}/{self.version_id}/{self.relative_path}"


class PrimaryAssetTag(SQLModel, table=True):
    __tablename__ = "v2_primary_asset_tag"
    tag_id: UUID = Field(
        index=True, primary_key=True, ondelete="CASCADE", foreign_key="tags.id"
    )
    primary_asset_id: UUID = Field(
        index=True,
        primary_key=True,
        ondelete="CASCADE",
        foreign_key="v2_primary_asset.id",
    )


class UserCache(SQLModel, table=True):
    __tablename__ = "user_cache"
    id: str = Field(
        primary_key=True
    )  # This is the auth0 ID in the form "auth0|1234567890"?
    full_name: str
    email: str
    created_versions: list["Version"] = Relationship(
        back_populates="creator",
    )
