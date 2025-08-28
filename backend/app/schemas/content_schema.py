from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from database.models_v1 import (
    DerivedContent,
    DocumentSource,
)
from database.models_v2 import Tag
from database.models_v2_enums import VersionStatus
from pydantic import BaseModel
from sqlmodel import SQLModel

DataT = TypeVar("DataT", bound=SQLModel)


class ListContentInput(BaseModel):
    latest_version_only: bool  # Purposely NOT optional to prevent unexpected behavior
    text: str | None = None
    limit: int | None = 20
    offset: int | None = 0
    sort_by: str | None = None
    sort_direction: str | None = "DESC"
    status: str | None = None
    content_type_name: list[str] | None = None
    order: int | None = None
    tags: list[str] | None = None
    tag_ids: list[str] | None = None
    version_id: list[str] | None = None


class ListContentTypesInput(BaseModel):
    limit: int | None = 20
    offset: int | None = 0
    sort_by: str | None = None
    sort_direction: str | None = "DESC"


class ListContentResult(BaseModel):
    id: UUID | None = None
    organization_id: str | None = None
    content_type_name: str | None = None
    # All content must be in a workspace currently
    content_name: str | None = None
    # Content doesn't need to be associated with a codebase in our flat asset design
    codebase_name: str | None = None
    relative_path: str | None = None
    content: str | None = None
    misc_metadata: dict | None = None
    status: VersionStatus | None = None
    tags: list[Tag] | None = None
    source_links: list[DocumentSource] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    source_content: Optional["DerivedContent"] = None
    order: int | None = None
    version_id: UUID | None = None
    version: str | None = None


class ListContentResults(BaseModel):
    results: list[ListContentResult]
    offset: int
    limit: int
    count: int


class TagAssociationRequest(BaseModel):
    tag_id: UUID
    include: bool


class TagAssociationResponse(BaseModel):
    tag_id: UUID
    content_id: UUID
    message: str


class BatchTagAssociationRequest(BaseModel):
    tags: list[TagAssociationRequest]


class BatchTagAssociationResponse(BaseModel):
    results: list[TagAssociationResponse]


class ContentResultBase(BaseModel, Generic[DataT]):
    results: list[DataT | None] = None


class ContentRequestBase(BaseModel, Generic[DataT]):
    result: DataT | None = None


class CreateContentResponse(ContentResultBase[DerivedContent]):
    pass


class ContentSourceResponse(ContentResultBase[ListContentResult]):
    pass


class CreateTemplateRequest(BaseModel):
    content_id: UUID


class CreateTemplateResponse(BaseModel):
    created: bool


class ContentCollectionAssociationRequest(BaseModel):
    collection_id: UUID


class BatchDeleteTagsRequest(BaseModel):
    tag_ids: list[UUID]


class DeleteTagItemResponse(BaseModel):
    content_id: UUID
    tag_id: UUID
    message: str


class BatchDeleteTagsResponse(BaseModel):
    results: list[DeleteTagItemResponse]


class DownloadContentResponse(BaseModel):
    download_url: str
    content_name: str
    status: str


class TagResult(BaseModel):
    id: UUID
    name: str
    color: str
    created_at: datetime
    updated_at: datetime


class ContentTagsResponse(BaseModel):
    tags: list[TagResult]


class ExportSingleRequest(BaseModel):
    content: str
