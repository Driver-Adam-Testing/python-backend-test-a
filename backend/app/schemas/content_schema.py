from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from database.models_v1 import (
    DerivedContent,
    DerivedContentType,
    DocumentSource,
    Enum_Derived_Content_Status,
    Tag,
)
from pydantic import BaseModel
from sqlmodel import SQLModel

DataT = TypeVar("DataT", bound=SQLModel)


class ListContentInput(BaseModel):
    text: str | None = None
    limit: int | None = 20
    offset: int | None = 0
    sort_by: str | None = None
    sort_direction: str | None = "DESC"
    status: str | None = None
    content_type_id: list[str] | None = None
    content_type_name: list[str] | None = None
    tags: list[str] | None = None
    tag_ids: list[str] | None = None


class ListContentTypesInput(BaseModel):
    limit: int | None = 20
    offset: int | None = 0
    sort_by: str | None = None
    sort_direction: str | None = "DESC"


class ListContentTypesResults(BaseModel):
    results: list[DerivedContentType]


class ListContentResult(BaseModel):
    id: UUID
    organization_id: str
    content_type_id: UUID
    content_type_name: str
    # All content must be in a workspace currently
    workspace_id: UUID
    workspace_name: str
    content_name: str
    source_content_id: UUID | None
    # Content doesn't need to be associated with a codebase in our flat asset design
    codebase_id: None | UUID
    codebase_name: str | None
    relative_path: str
    content: None | str
    misc_metadata: dict | None
    status: Enum_Derived_Content_Status | None
    tags: list[Tag]
    source_links: list[DocumentSource] | None
    created_at: None | datetime
    updated_at: None | datetime
    source_content: Optional["DerivedContent"]
    order: int | None


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


class CreateContentRequest(BaseModel):
    workspace_id: UUID | None = None
    codebase_id: UUID | None = None
    content_type: str


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


class ContentSourceAssociationRequest(BaseModel):
    include: bool


class ContentSourceAssociationItem(BaseModel):
    source_content_id: UUID
    include: bool


class ContentCollectionAssociationRequest(BaseModel):
    collection_id: UUID


class BatchContentSourceAssociationRequest(BaseModel):
    sources: list[ContentSourceAssociationItem]


class DeleteContentSourcesRequest(BaseModel):
    source_ids: list[UUID]


class ContentSourceAssociationResponse(BaseModel):
    content_id: UUID
    source_id: UUID
    message: str


class BatchContentSourceAssociationResponse(BaseModel):
    content_id: UUID
    sources: list[ContentSourceAssociationItem]
    message: str


class DeleteDocumentSourceResponse(BaseModel):
    document_id: UUID
    source_id: UUID
    message: str


class BatchDeleteDocumentSourceResponse(BaseModel):
    results: list[DeleteDocumentSourceResponse]


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
