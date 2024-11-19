from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Computed, DateTime, ForeignKey, Index, Integer, func
from sqlalchemy.dialects.postgresql import UUID as SaUuid
from sqlmodel import Field, Relationship, Session, SQLModel, select, text

from .custom_types import TSVector


class PrimaryAssetRow(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_primary_asset"

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


class VersionRow(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_version"

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


class NodeRow(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_version_node"

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
    relative_path: str
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
    contents: list["ContentRow"] = Relationship(back_populates="node")


class FullNodeView(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_full_node"
    __view_creation__ = text("""
            CREATE VIEW v2_full_node AS
            SELECT
                pa.id AS primary_asset_id,
                pa.display_name AS primary_asset_display_name,
                pa.organization_id AS primary_asset_organization_id,
                pa.created_at AS primary_asset_created_at,
                pa.updated_at AS primary_asset_updated_at,
                v.id AS version_id,
                v.display_name AS version_display_name,
                v.created_at AS version_created_at,
                v.updated_at AS version_updated_at,
                n.id AS node_id,
                n.relative_path AS node_relative_path,
                n.created_at AS node_created_at,
                n.updated_at AS node_updated_at
            FROM
                v2_primary_asset pa
            LEFT JOIN
                v2_version v ON pa.id = v.primary_asset_id
            LEFT JOIN
                v2_version_node n ON v.id = n.version_id
            """)
    primary_asset_id: UUID | None = Field(default=None, primary_key=True)
    primary_asset_display_name: str | None = Field(default=None)
    primary_asset_organization_id: str | None = Field(default=None)
    primary_asset_created_at: None | datetime = Field(default=None)
    primary_asset_updated_at: None | datetime = Field(default=None)
    version_id: UUID | None = Field(default=None)
    version_display_name: str | None = Field(default=None)
    version_created_at: None | datetime = Field(default=None)
    version_updated_at: None | datetime = Field(default=None)
    node_id: UUID | None = Field(default=None)
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


class ContentRow(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_content"

    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    version_node_id: UUID = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            ForeignKey("v2_version_node.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    text: str
    content_type: str
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

    node: "NodeRow" = Relationship(back_populates="contents")
    chunks: list["ChunkRow"] = Relationship(back_populates="content")


class ChunkRow(SQLModel, table=True):  # type: ignore
    __tablename__ = "v2_chunk"

    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    content_id: UUID = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            ForeignKey("v2_content.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    text: str
    text_embedding_3_small: list[float] = Field(
        sa_column=Column(Vector(1536), nullable=True)
    )
    chunk_number: int = Field(sa_column=Column(Integer, nullable=False))
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

    content: "ContentRow" = Relationship(back_populates="chunks")

    __ts_vector__: any = Column(
        "__ts_vector__",
        TSVector(),
        Computed("to_tsvector('english', text)", persisted=True),
    )
    __table_args__ = (
        Index("ix_chunk___ts_vector__", __ts_vector__, postgresql_using="gin"),
    )
