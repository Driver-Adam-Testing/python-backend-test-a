from dataclasses import Field
from datetime import datetime
from symtable import Class
from typing import Optional, Generic
from uuid import UUID
from sqlmodel import Session, SQLModel, select, asc, desc
from typing import Type, TypeVar, Generic, Optional, List, Any
from pydantic import BaseModel, ConfigDict

from database.models_v1 import (
    DerivedContent,
    DerivedContentType,
    Enum_Derived_Content_Status,
    Tag,
    TagContent,
    Workspace,
)


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
    relative_path: str
    content: None | str
    misc_metadata: dict | None
    status: Enum_Derived_Content_Status | None
    tags: list[Tag]
    created_at: None | datetime
    updated_at: None | datetime
    source_content: Optional["DerivedContent"]
    order: int | None


class ListContentResults(BaseModel):
    results: list[ListContentResult]
    offset: int
    limit: int
    count: int


class TagAssociationResponse(BaseModel):
    tag_id: str
    content_id: str
    message: str


class CreateContentRequest(BaseModel):
    workspace_id: str
    codebase_id: str


class ContentResultBase(BaseModel, Generic[DataT]):
    results: list[Optional[DataT]] = None


class CreateContentResponse(ContentResultBase[DerivedContent]):
    pass


class CreateTemplateRequest(BaseModel):
    content_id: str


class CreateTemplateResponse(BaseModel):
    created: bool
