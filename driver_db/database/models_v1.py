import enum
import functools
import uuid
from datetime import UTC, datetime
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


class ContentMetadata(SQLModel, table=True):  # type: ignore
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
    workspace_id: UUID = Field(index=True)
    codebase_id: UUID | None = Field(default=None, nullable=True, index=True)
    content_type: ContentType = Field(Enum(ContentType), index=True)
    relative_path: str | None = Field(default=None, nullable=True, index=True)
    misc_metadata: dict = Field(default={}, sa_column=Column(JSON, nullable=False))  # type: ignore
    chunks: list["Chunk"] = Relationship(back_populates="content_metadata")


# TODO deprecate once all embeddings are in ChunkAndEmbedding
class Chunk(SQLModel, table=True):  # type: ignore
    # TODO Note: these timestamps weren't updated to match the others because this
    # table is deprecated soon and there were tons of rows to populate.
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            default=functools.partial(datetime.now, tz=UTC),
            nullable=True,
        ),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            onupdate=functools.partial(datetime.now, tz=UTC),
            nullable=True,
        ),
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    content_metadata_id: UUID = Field(
        foreign_key="contentmetadata.id", nullable=False, index=True
    )
    content_metadata: ContentMetadata = Relationship(back_populates="chunks")
    text: str
    # Text Embeddings are actually indexed but it's not reflected in the model.py because it's using ivfflat
    text_embedding_3_small: list[float] = Field(
        sa_column=Column(Vector(1536), nullable=True)
    )
    chunk_number: int | None
    token_count: int | None
    line_number: int | None


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
    workspace_id: str
    codebase_id: str | None
    model: str
    messages: list["RuntimeLogAgentMessage"] = Relationship(
        back_populates="agent_instance"
    )
    errors: list["RuntimeLogAgentError"] = Relationship(back_populates="agent_instance")
    content_retrievals: list["RuntimeLogContentRetrieval"] = Relationship(
        back_populates="agent_instance"
    )


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


class RuntimeLogAgentError(SQLModel, table=True):  # type: ignore
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_instance_id: UUID = Field(
        foreign_key="runtimelogagentinstance.id", nullable=False
    )
    agent_instance: RuntimeLogAgentInstance = Relationship(back_populates="errors")
    error: str


class RuntimeLogContentRetrieval(SQLModel, table=True):  # type: ignore
    created_at: None | datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
        default=None,
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_instance_id: UUID = Field(
        foreign_key="runtimelogagentinstance.id", nullable=False
    )
    agent_instance: RuntimeLogAgentInstance = Relationship(
        back_populates="content_retrievals"
    )
    chunk_id: UUID = Field(foreign_key="chunk.id", nullable=False)


# class RuntimeLogOperation(SQLModel, table=True):  # type: ignore
# TODO this need to match the other created_at columns!
#     created_at: datetime = Field(
#         default=None,
#         sa_column=Column(
#             DateTime(timezone=True),
#             default=functools.partial(datetime.now, tz=timezone.utc),
#             nullable=True,
#         ),
#     )
#     id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
#     name: str
#     request: dict = Field(default={}, sa_column=Column(JSON, nullable=True))


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
    include: None | bool = Field(default=None)
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
    include: None | bool = Field(default=None)
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

    __ts_vector__: None | any = Column(
        "__ts_vector__",
        TSVector(),
        Computed("to_tsvector('english', text)", persisted=True),
    )
    __table_args__ = (
        Index(
            "ix_chunkandembedding___ts_vector__", __ts_vector__, postgresql_using="gin"
        ),
    )
