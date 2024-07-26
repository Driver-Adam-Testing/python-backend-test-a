from datetime import date, datetime
from uuid import UUID

import strawberry
from database.models_v1 import (
    Codebase,
    DerivedContent,
    DerivedContentType,
    Llm,
    SourceContent,
    SourceContentType,
    Workspace,
)

from app.api.routes.legacy.scalars import ID


@strawberry.input
class LimitOffsetPagination:
    limit: int = 100
    offset: int = 0


@strawberry.input
class ContentMetadataQuery:
    id: UUID | None = None
    workspace_id: UUID | None = None
    codebase_id: UUID | None = None
    content_type: str | None = None
    relative_path: str | None = None


@strawberry.input
class ChunkQuery:
    id: UUID | None = None
    content_metadata_id: UUID | None = None
    text: str | None = None
    chunk_number: int | None = None
    token_count: int | None = None
    line_number: int | None = None


@strawberry.input
class RuntimeLogAgentInstanceQuery:
    id: UUID | None = None
    workspace_id: str | None = None
    codebase_id: str | None = None
    model: str | None = None


@strawberry.input
class RuntimeLogAgentMessageQuery:
    id: UUID | None = None
    message: dict | None = None
    order: int | None = None
    agent_instance_id: UUID | None = None


@strawberry.input
class RuntimeLogAgentErrorQuery:
    id: UUID | None = None
    agent_instance_id: UUID | None = None
    error: str | None = None


@strawberry.input
class RuntimeLogContentRetrievalQuery:
    id: UUID | None = None
    agent_instance_id: UUID | None = None
    chunk_id: UUID | None = None


@strawberry.input
class WorkspaceQuery:
    __model__ = Workspace
    id: UUID | None = None
    display_name: str | None = None
    description: str | None = None


@strawberry.input
class CodebaseQuery:
    __model__ = Codebase
    id: UUID | None = None
    codebase_name: str | None = None
    description: str | None = None
    status: str | None = None
    storage_url: str | None = None
    resource_root: str | None = None
    creator_id: str | None = None
    workspace: WorkspaceQuery | None = None


@strawberry.input
class SourceContentTypeQuery:
    __model__ = SourceContentType
    id: UUID | None = None
    type_name: str | None = None


@strawberry.input
class SourceContentQuery:
    __model__ = SourceContent
    id: UUID | None = None
    workspace: WorkspaceQuery | None = None
    codebase: CodebaseQuery | None = None
    source_content_type: SourceContentTypeQuery | None = None


@strawberry.input
class LlmQuery:
    __model__ = Llm
    id: UUID | None = None
    name: str | None = None
    model: str | None = None
    training_date: date | None = None
    owned_by: str | None = None


@strawberry.input
class DerivedContentTypeQuery:
    __model__ = DerivedContentType
    id: UUID | None = None
    type_name: str | None = None


@strawberry.input
class DerivedContentQuery:
    __model__ = DerivedContent
    id: UUID | None = None
    content: str | None = None
    misc_metadata: dict | None = None
    status: str | None = None
    order: int | None = None
    llm: LlmQuery | None = None
    source_content: SourceContentQuery | None = None
    derived_content_type: DerivedContentTypeQuery | None = None


@strawberry.experimental.pydantic.type(Workspace, all_fields=True)
class WorkspaceResults:
    @strawberry.experimental.pydantic.type(Codebase, all_fields=True)
    class WorkspaceCodebaseResults:
        pass

    codebases: list[WorkspaceCodebaseResults]


# type: ignore
@strawberry.experimental.pydantic.type(Llm, all_fields=True)
class LlmResults:
    pass


# type: ignore
@strawberry.experimental.pydantic.type(DerivedContentType, all_fields=True)
class DerivedContentTypeResults:
    pass


# type: ignore
@strawberry.experimental.pydantic.type(DerivedContent, all_fields=True)
class DerivedContentResults:
    @strawberry.field(description="Metadata of the derived content")
    def metadata(self) -> dict | None:
        return self.misc_metadata  # type: ignore

    derived_content_type: DerivedContentTypeResults

    @strawberry.experimental.pydantic.type(SourceContent, all_fields=True)
    class DerivedContentSourceContentResults:
        pass

    source_content: DerivedContentSourceContentResults

    llm: LlmResults | None


# type: ignore
@strawberry.experimental.pydantic.type(SourceContentType, all_fields=True)
class SourceContentTypeResults:
    pass


# type: ignore
@strawberry.experimental.pydantic.type(SourceContent, all_fields=True)
class SourceContentResults:
    source_content_type: SourceContentTypeResults
    workspace: WorkspaceResults

    @strawberry.experimental.pydantic.type(Codebase, all_fields=True)
    class SourceContentCodebaseResults:
        pass

    codebase: SourceContentCodebaseResults | None
    derived_contents: list[DerivedContentResults]


# type: ignore
@strawberry.experimental.pydantic.type(Codebase, all_fields=True)
class CodebaseResults:
    pass


# type: ignore
@strawberry.experimental.pydantic.input(Workspace, all_fields=True)
class WorkspaceInput:
    pass


# type: ignore
@strawberry.experimental.pydantic.input(DerivedContent, all_fields=True)
class DerivedContentInput:
    pass


# type: ignore
@strawberry.input
class SourceContentInput:
    workspace_id: UUID | None = None
    codebase_id: UUID | None = None
    relative_path: str | None = None
    source_content_type: str | None = None


# type: ignore
@strawberry.experimental.pydantic.input(Codebase, all_fields=True)
class CodebaseInput:
    pass


@strawberry.type
class OrganizationResult:
    id: str
    name: str
    display_name: str
    workspaces: list[WorkspaceResults]  # Specify the type of elements in the list


@strawberry.type
class SupplementalContent:
    id: ID
    name: str
    relative_path: str
    download_url: str
    created_at: datetime | None = None
    file_size_bytes: int | None = None
    pages: int | None = None


@strawberry.type
class GitProvider:
    display_name: str
    name: str
    logo_url: str


@strawberry.type
class GitRepository:
    provider_name: str
    repo_name: str
    org: str
    last_updated: datetime
    metadata: dict
