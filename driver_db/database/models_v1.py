import enum
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy.dialects.postgresql
import strawberry
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    Computed,
    DateTime,
    Enum,
    Index,
    Integer,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SaUuid
from sqlmodel import JSON, Field, Relationship, SQLModel

from .custom_types import TSVector


# TODO remove in favor of derived content types once new embeddings created
class ContentType(str, enum.Enum):
    SOURCE_CODE = "SOURCE_CODE"
    AUXILIARY_DOCUMENTATION = "AUXILIARY_DOCUMENTATION"
    FILE_SUMMARY = "FILE_SUMMARY"
    FOLDER_SUMMARY = "FOLDER_SUMMARY"
    CODE_SYMBOL = "CODE_SYMBOL"
    PDF_SUMMARY = "PDF_SUMMARY"
    UNKNOWN = "UNKNOWN"


class RuntimeLogAgentInstance(SQLModel, table=True):  # type: ignore
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
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: str | None
    codebase_id: str | None
    model: str
    messages: list["RuntimeLogAgentMessage"] = Relationship(
        back_populates="agent_instance"
    )
    organization_id: str | None


class RuntimeLogAgentMessage(SQLModel, table=True):  # type: ignore
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    message: dict = Field(default={}, sa_column=Column(JSON, nullable=False))  # type: ignore
    order: int = Field(default=None, sa_column=Column(Integer, autoincrement=True))
    agent_instance_id: UUID = Field(
        foreign_key="runtimelogagentinstance.id", nullable=False
    )
    agent_instance: RuntimeLogAgentInstance = Relationship(back_populates="messages")


@strawberry.enum
class Enum_Derived_Content_Status(str, enum.Enum):
    generating = "generating"
    generation_complete = "generation-complete"
    generation_error = "generation-error"


@strawberry.enum
class Enum_Codebase_Status(str, enum.Enum):
    processing = "processing"
    processing_complete = "processing-complete"
    processing_error = "processing-error"
    codebase_rejected = "codebase-rejected"

    def into_dc_status(self) -> Enum_Derived_Content_Status:
        match self:
            case Enum_Codebase_Status.processing:
                return Enum_Derived_Content_Status.generating
            case Enum_Codebase_Status.processing_complete:
                return Enum_Derived_Content_Status.generation_complete
            case Enum_Codebase_Status.processing_error:
                return Enum_Derived_Content_Status.generation_error
            case _:
                raise ValueError(f"No valid mapping for status: {self}")


class Workspace(SQLModel, table=True):  # type: ignore
    __tablename__ = "workspaces"
    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    display_name: None | str = Field(
        max_length=255,
        sa_column=sqlalchemy.Column(sqlalchemy.String(255), nullable=True),
    )
    description: None | str = None
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
    )
    codebases: list["Codebase"] = Relationship(back_populates="workspace")
    source_contents: list["DerivedContent"] = Relationship(back_populates="workspace")


class Codebase(SQLModel, table=True):  # type: ignore
    __tablename__ = "codebases"
    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            "workspace_id", "codebase_name", name="uq_workspace_id_codebase_name"
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
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)
    codebase_name: str = Field(
        max_length=255,
        sa_column=sqlalchemy.Column(sqlalchemy.String(255), nullable=False),
    )
    description: None | str = Field(sa_column=Column(sqlalchemy.Text, nullable=True))
    status: Enum_Codebase_Status = Field(
        sa_column=sqlalchemy.Column(
            Enum(Enum_Codebase_Status, values_callable=lambda x: [e.value for e in x]),
            nullable=False,
        )
    )  # TODO this makes the enum values the strings to match sequelize versions.
    # Normally we wouldn't need to define the field at all
    storage_url: None | str = Field(sa_column=Column(sqlalchemy.Text, nullable=True))
    resource_root: None | str = Field(sa_column=Column(sqlalchemy.Text, nullable=True))
    creator_id: str | None
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
    )
    workspace: Workspace = Relationship(back_populates="codebases")
    source_contents: list["DerivedContent"] = Relationship(back_populates="codebase")


class DerivedContentType(SQLModel, table=True):  # type: ignore
    __tablename__ = "derived_content_types"
    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    type_name: str = Field(
        max_length=255,
        sa_column=sqlalchemy.Column(
            sqlalchemy.String(255), unique=True, nullable=False
        ),
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
    )
    contents: list["DerivedContent"] = Relationship(back_populates="content_type")


class TagContent(SQLModel, table=True):
    __tablename__ = "tags_contents"
    """Link table between Tags and Content models."""

    tag_id: None | uuid.UUID = Field(
        default=None, foreign_key="tags.id", primary_key=True
    )
    include: bool
    content_id: None | uuid.UUID = Field(
        default=None, foreign_key="derived_contents.id", primary_key=True
    )
    tag: Optional["Tag"] = Relationship(
        back_populates="content_links",
        sa_relationship_kwargs={"foreign_keys": "TagContent.tag_id"},
    )
    content: Optional["DerivedContent"] = Relationship(
        back_populates="tag_links",
        sa_relationship_kwargs={"foreign_keys": "TagContent.content_id"},
    )


class DocumentSource(SQLModel, table=True):
    __tablename__ = "document_sources"
    """Link table between documents and their sources."""

    document_id: None | uuid.UUID = Field(
        default=None, foreign_key="derived_contents.id", primary_key=True
    )
    include: bool
    source_id: None | uuid.UUID = Field(
        default=None, foreign_key="derived_contents.id", primary_key=True
    )
    document: "DerivedContent" = Relationship(
        back_populates="source_links",
        sa_relationship_kwargs={"foreign_keys": "DocumentSource.document_id"},
    )
    source: "DerivedContent" = Relationship(
        back_populates="document_links",
        sa_relationship_kwargs={"foreign_keys": "DocumentSource.source_id"},
    )


# TODO add indexes back
class DerivedContent(SQLModel, table=True):  # type: ignore
    __tablename__ = "derived_contents"
    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    content_type_id: UUID = Field(
        foreign_key="derived_content_types.id", nullable=False, index=True
    )
    content_type: DerivedContentType = Relationship(back_populates="contents")
    # All content must be in a workspace
    workspace_id: UUID = Field(foreign_key="workspaces.id", nullable=False, index=True)
    source_content_id: UUID | None = Field(
        foreign_key="derived_contents.id", index=True, nullable=True, default=None
    )
    # Content doesn't need to be associated with a codebase in our flat asset design. But for now, we keep
    # all source contents and derived contents for a codebase associated with the codebase. PDFs and other docs,
    # however, won't have a codebase ID -- just a workspace ID, since we are keeping workspaces for now.
    codebase_id: None | UUID = Field(
        default=None, foreign_key="codebases.id", nullable=True, index=True
    )

    codebase: None | Codebase = Relationship(back_populates="source_contents")
    relative_path: str = Field(
        sa_column=Column(sqlalchemy.Text, nullable=False, index=True)
    )
    content: None | str = Field(
        sa_column=Column(sqlalchemy.Text, nullable=True), default=None
    )
    content_name: None | str = Field(
        sa_column=Column(sqlalchemy.Text, nullable=True), default=None
    )
    misc_metadata: dict | None = Field(  # type: ignore
        sa_column=Column("metadata", JSONB, nullable=True), default=None
    )
    status: Enum_Derived_Content_Status | None = Field(
        sa_column=sqlalchemy.Column(
            Enum(
                Enum_Derived_Content_Status,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=True,
        ),
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
    )
    source_content: Optional["DerivedContent"] = Relationship(
        back_populates="derived_contents",
        sa_relationship_kwargs={"remote_side": "DerivedContent.id"},
    )
    derived_contents: list["DerivedContent"] = Relationship(
        back_populates="source_content"
    )
    order: int | None = Field(
        sa_column=Column(Integer, nullable=True, server_default=text("0"))
    )
    workspace: Workspace = Relationship(back_populates="source_contents")
    document_links: list["DocumentSource"] = Relationship(
        back_populates="source",
        sa_relationship_kwargs={"foreign_keys": "DocumentSource.source_id"},
    )

    source_links: list["DocumentSource"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"foreign_keys": "DocumentSource.document_id"},
    )
    chunks_and_embeds: list["ChunkAndEmbedding"] = Relationship(
        back_populates="content", cascade_delete=True
    )

    tag_links: list["TagContent"] = Relationship(back_populates="content")
    tags: list["Tag"] = Relationship(
        back_populates=None,
        sa_relationship_kwargs={"secondary": "tags_contents", "viewonly": True},
    )
    version_id: None | UUID = Field(
        foreign_key="inspection_versions.id", nullable=True, index=True, default=None
    )
    inspection_version: Optional["InspectionVersion"] = Relationship(
        back_populates="contents"
    )


class Tag(SQLModel, table=True):  # type: ignore
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="unique_tag_name_per_org_id"),
    )
    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    name: str = Field(
        max_length=255,
        sa_column=sqlalchemy.Column(sqlalchemy.String(255), nullable=False),
    )
    hex_color: str = Field(
        max_length=7,
        sa_column=sqlalchemy.Column(sqlalchemy.String(7), nullable=False),
    )
    organization_id: str
    type: str = Field(
        max_length=255,
        sa_column=sqlalchemy.Column(sqlalchemy.String(255), nullable=False),
    )
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    created_by: None | datetime = Field(
        sa_column=sqlalchemy.Column(sqlalchemy.String(128), nullable=False),
        default=None,
    )
    updated_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )
    updated_by: None | datetime = Field(
        sa_column=sqlalchemy.Column(sqlalchemy.String(128), nullable=False),
        default=None,
    )
    content_links: list["TagContent"] = Relationship(
        back_populates="tag",
        sa_relationship_kwargs={"foreign_keys": "TagContent.tag_id"},
    )


class ChunkAndEmbedding(SQLModel, table=True):  # type: ignore
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    content_id: UUID = Field(
        foreign_key="derived_contents.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    content: DerivedContent | None = Relationship(back_populates="chunks_and_embeds")
    text: str
    text_embedding_3_small: list[float] = Field(
        sa_column=Column(
            Vector(1536), nullable=True
        )  # TODO this column will need to be indexed ONCE POPULATED1
    )
    chunk_number: int
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
    )

    __ts_vector__: any = Column(
        "__ts_vector__",
        TSVector(),
        Computed("to_tsvector('english', text)", persisted=True),
    )
    __table_args__ = (
        Index(
            "ix_chunkandembedding___ts_vector__", __ts_vector__, postgresql_using="gin"
        ),
    )


class InspectionVersion(SQLModel, table=True):
    __tablename__ = "inspection_versions"

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    version: str  # Typically a Git commit hash
    display_name: str | None = (
        None  # User-defined name; could default to Git tags if available
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
    )
    previous_version_id: UUID | None = Field(
        foreign_key="inspection_versions.id", nullable=True
    )  # Points to the previous version for chain tracking
    contents: list["DerivedContent"] = Relationship(back_populates="inspection_version")
    inspector_runs: list["InspectorRun"] = Relationship(
        back_populates="inspection_version"
    )


class InspectorRun(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    inspection_version_id: UUID = Field(
        foreign_key="inspection_versions.id", nullable=False
    )
    inspection_version: "InspectionVersion" = Relationship(
        back_populates="inspector_runs"
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
    )


class UsageSessionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UsageSession(SQLModel, table=True):
    __tablename__ = "usage_sessions"
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: UsageSessionStatus = Field(default=UsageSessionStatus.PENDING, index=True)
    organization_id: str
    user_id: str
    session_metadata: dict | None = Field(
        sa_column=Column("metadata", JSONB, nullable=True), default=None
    )
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    updated_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )

    usage_events: list["UsageEvent"] = Relationship(back_populates="session")


class UsageEventType(enum.IntEnum):
    AGENT_PIPELINE_USAGE_DEBIT = 1
    INSPECTOR_TECH_DOC_USAGE_DEBIT = 2
    INSPECTOR_CODE_DIFF_USAGE_DEBIT = 3
    ONBOARDING_USAGE_DEBIT = 4
    SUMMARIZATION_USAGE_DEBIT = 5
    BASE_PLATFORM_USAGE_CREDIT = 6
    ADDITIONAL_PLATFORM_USAGE_CREDIT = 7


class UsageEvent(SQLModel, table=True):
    __tablename__ = "usage_events"
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    event_type: UsageEventType = Field(sa_column=Column(Integer, nullable=False))
    session_id: UUID = Field(
        foreign_key="usage_sessions.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    organization_id: str
    user_id: str
    event_source: str
    bytes_in: int = Field(default=0, nullable=False)
    bytes_out: int = Field(default=0, nullable=False)
    tokens_in: int = Field(default=0, nullable=False)
    tokens_out: int = Field(default=0, nullable=False)
    timestamp: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    event_metadata: dict | None = Field(
        sa_column=Column("metadata", JSONB, nullable=True), default=None
    )
    # Relationships
    session: UsageSession | None = Relationship(back_populates="usage_events")
