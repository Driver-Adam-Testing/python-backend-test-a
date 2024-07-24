import enum
import functools
import uuid
from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy.dialects.postgresql
import strawberry
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Enum, Integer, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SaUuid
from sqlmodel import JSON, Field, Relationship, SQLModel


class ContentType(str, enum.Enum):
    SOURCE_CODE = "SOURCE_CODE"
    AUXILIARY_DOCUMENTATION = "AUXILIARY_DOCUMENTATION"
    FILE_SUMMARY = "FILE_SUMMARY"
    FOLDER_SUMMARY = "FOLDER_SUMMARY"
    CODE_SYMBOL = "CODE_SYMBOL"
    PDF_SUMMARY = "PDF_SUMMARY"
    UNKNOWN = "UNKNOWN"


# TODO: index content_type


class ContentMetadata(SQLModel, table=True):  # type: ignore
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            default=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
        ),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            onupdate=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
        ),
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: UUID = Field(index=True)
    codebase_id: UUID | None = Field(default=None, nullable=True, index=True)
    content_type: ContentType = Enum(ContentType)
    relative_path: str | None = Field(default=None, nullable=True, index=True)
    misc_metadata: dict = Field(default={}, sa_column=Column(JSON, nullable=False))  # type: ignore
    chunks: list["Chunk"] = Relationship(back_populates="content_metadata")


class Chunk(SQLModel, table=True):  # type: ignore
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            default=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
        ),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            onupdate=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
        ),
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    content_metadata_id: UUID = Field(foreign_key="contentmetadata.id", nullable=False)
    content_metadata: ContentMetadata = Relationship(back_populates="chunks")
    text: str
    text_embedding_3_small: list[float] = Field(
        sa_column=Column(Vector(1536), nullable=True)
    )
    chunk_number: int | None
    token_count: int | None
    line_number: int | None


class RuntimeLogAgentInstance(SQLModel, table=True):  # type: ignore
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            default=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
        ),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            onupdate=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
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
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            default=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
        ),
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    message: dict = Field(default={}, sa_column=Column(JSON, nullable=False))  # type: ignore
    order: int = Field(default=None, sa_column=Column(Integer, autoincrement=True))
    agent_instance_id: UUID = Field(
        foreign_key="runtimelogagentinstance.id", nullable=False
    )
    agent_instance: RuntimeLogAgentInstance = Relationship(back_populates="messages")


class RuntimeLogAgentError(SQLModel, table=True):  # type: ignore
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            default=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
        ),
    )
    id: UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_instance_id: UUID = Field(
        foreign_key="runtimelogagentinstance.id", nullable=False
    )
    agent_instance: RuntimeLogAgentInstance = Relationship(back_populates="errors")
    error: str


class RuntimeLogContentRetrieval(SQLModel, table=True):  # type: ignore
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            default=functools.partial(datetime.now, tz=timezone.utc),
            nullable=True,
        ),
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


class SetupCompleted(SQLModel, table=True):  # type: ignore
    __tablename__ = "setup_completed"
    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )


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
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
        default=None,
    )

    updated_at: None | datetime = Field(
        sa_column=Column(DateTime(timezone=False), onupdate=func.now()), default=None
    )
    codebases: list["Codebase"] = Relationship(back_populates="workspace")
    # source_contents: list["SourceContent"] = Relationship(back_populates="workspace")


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
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
        default=None,
    )

    updated_at: None | datetime = Field(
        sa_column=Column(DateTime(timezone=False), onupdate=func.now()), default=None
    )
    workspace: Workspace = Relationship(back_populates="codebases")
    source_contents: list["SourceContent"] = Relationship(back_populates="codebase")


class SourceContentType(SQLModel, table=True):  # type: ignore
    __tablename__ = "source_content_types"
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
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
        default=None,
    )

    updated_at: None | datetime = Field(
        sa_column=Column(DateTime(timezone=False), onupdate=func.now()), default=None
    )
    # source_contents: list["SourceContent"] = Relationship(
    #     back_populates="source_content_type"
    # )


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
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
        default=None,
    )

    updated_at: None | datetime = Field(
        sa_column=Column(DateTime(timezone=False), onupdate=func.now()), default=None
    )
    derived_contents: list["DerivedContent"] = Relationship(
        back_populates="derived_content_type"
    )


class SourceContent(SQLModel, table=True):  # type: ignore
    __tablename__ = "source_contents"
    id: UUID | None = Field(
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
        default=None,
    )
    content_type_id: UUID  # FK dropped in prep for copy from SC -> DC
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)
    codebase_id: None | UUID = Field(
        default=None, foreign_key="codebases.id", index=True
    )
    relative_path: str = Field(sa_column=Column(sqlalchemy.Text, nullable=False))
    created_at: None | datetime = Field(
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
        default=None,
    )

    updated_at: None | datetime = Field(
        sa_column=Column(DateTime(timezone=False), onupdate=func.now()), default=None
    )
    misc_metadata: dict | None = Field(  # type: ignore
        sa_column=Column("metadata", JSONB, nullable=True), default=None
    )
    # source_content_type: SourceContentType = Relationship(
    #     back_populates="source_contents"
    # )
    workspace: Workspace = Relationship(back_populates="source_contents")
    codebase: None | Codebase = Relationship(back_populates="source_contents")
    # derived_contents: list["DerivedContent"] = Relationship(
    #     back_populates="source_content"
    # )
    order: int | None = Field(
        sa_column=Column(Integer, nullable=True, server_default=text("0"))
    )
    content: None | str = Field(sa_column=Column(sqlalchemy.Text, nullable=True))
    status: Enum_Derived_Content_Status = Field(
        sa_column=sqlalchemy.Column(
            Enum(
                Enum_Derived_Content_Status,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=True,
        )
    )


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
    content_type_id: UUID = Field(foreign_key="derived_content_types.id")
    workspace_id: UUID = Field(foreign_key="workspaces.id", nullable=False)
    source_content_id: UUID | None = Field(
        foreign_key="source_contents.id", index=True, nullable=True, default=None
    )
    codebase_id: None | UUID = Field(default=None, foreign_key="codebases.id")
    relative_path: str = Field(sa_column=Column(sqlalchemy.Text, nullable=False))
    content: None | str = Field(sa_column=Column(sqlalchemy.Text, nullable=True))
    misc_metadata: dict | None = Field(  # type: ignore
        sa_column=Column("metadata", JSONB, nullable=True), default=None
    )  # Rename of attr required since metadata is a reserved keyword
    status: Enum_Derived_Content_Status = Field(
        sa_column=sqlalchemy.Column(
            Enum(
                Enum_Derived_Content_Status,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=True,
        )
    )
    created_at: None | datetime = Field(
        sa_column=Column(DateTime(timezone=False), server_default=func.now()),
        default=None,
    )

    updated_at: None | datetime = Field(
        sa_column=Column(DateTime(timezone=False), onupdate=func.now()), default=None
    )
    # derived_content_type: DerivedContentType = Relationship(
    #     back_populates="derived_contents"
    # )
    # source_content: SourceContent = Relationship(back_populates="derived_contents")
    order: int | None = Field(
        sa_column=Column(Integer, nullable=True, server_default=text("0"))
    )
