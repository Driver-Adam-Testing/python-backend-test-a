from datetime import datetime
from uuid import UUID

import strawberry
from app.api.routes.legacy.scalars import ID


@strawberry.input
class LimitOffsetPagination:
    limit: int = 100
    offset: int = 0


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


# type: ignore
@strawberry.input
class SourceContentInput:
    workspace_id: UUID | None = None
    codebase_id: UUID | None = None
    relative_path: str | None = None
    source_content_type: str | None = None


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
