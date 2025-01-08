# node_schemas.py
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from database.models_v2_enums import (
    ContentKind,
    NodeKind,
    PrimaryAssetKind,
)
from pydantic import BaseModel

T = TypeVar("T")


class ListWithCount(BaseModel, Generic[T]):
    results: list[T]
    total_count: int


#####################
# FLAT READ SCHEMAS #
#####################


class PrimaryAssetRead(BaseModel):
    id: UUID
    organization_id: str
    kind: PrimaryAssetKind
    display_name: str
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        orm_mode = True


class VersionRead(BaseModel):
    id: UUID
    primary_asset_id: UUID
    display_name: str
    created_at: datetime | None
    updated_at: datetime | None
    status: str | None

    class Config:
        orm_mode = True


class NodeRead(BaseModel):
    id: UUID
    version_id: UUID
    relative_path: str
    kind: NodeKind
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        orm_mode = True


class TagRead(BaseModel):
    id: UUID
    name: str
    hex_color: str
    organization_id: str
    type: str
    created_at: datetime | None
    created_by: str
    updated_at: datetime | None
    updated_by: str

    class Config:
        orm_mode = True


class PrimaryAssetTagRead(BaseModel):
    tag_id: UUID
    primary_asset_id: UUID

    class Config:
        orm_mode = True


class ContentRead(BaseModel):
    id: UUID | None
    node_id: UUID | None
    content: str | None
    misc_metadata: dict | None
    created_at: datetime | None
    updated_at: datetime | None


class DocumentSourceRead(BaseModel):
    page_node_id: UUID | None
    source_node_id: UUID | None


#######################
# DETAIL READ SCHEMAS #
#######################


class NodeDetailRead(NodeRead):
    class NodeVersionRead(VersionRead):
        primary_asset: PrimaryAssetRead

    version: NodeVersionRead


class VersionDetailRead(VersionRead):
    primary_asset: PrimaryAssetRead
    root_node: NodeRead | None


class PrimaryAssetDetailRead(PrimaryAssetRead):
    class PrimaryAssetVersionRead(VersionRead):
        root_node: NodeRead | None

    versions: list[PrimaryAssetVersionRead] | None
    tags: list[TagRead] | None


class PrimaryAssetTagDetailRead(PrimaryAssetTagRead):
    primary_asset: PrimaryAssetRead


class ContentDetailRead(ContentRead):
    node: NodeDetailRead


class DocumentSourceDetailRead(DocumentSourceRead):
    source_node: NodeDetailRead


class TagDetailRead(TagRead):
    primary_assets: list[PrimaryAssetRead]


# Create and Update Schemas


class PrimaryAssetCreate(BaseModel):
    display_name: str
    kind: PrimaryAssetKind


class PrimaryAssetUpdate(BaseModel):
    display_name: str | None = None


class VersionCreate(BaseModel):
    primary_asset_id: UUID
    display_name: str


class VersionUpdate(BaseModel):
    display_name: str | None = None


class NodeCreate(BaseModel):
    version_id: UUID
    relative_path: str


class NodeUpdate(BaseModel):
    relative_path: str | None = None


class TagCreate(BaseModel):
    name: str
    hex_color: str
    type: str


class ContentCreate(BaseModel):
    node_id: UUID
    content_kind: ContentKind
    content: str | None = None
    misc_metadata: dict | None = None


class DerivedContentUpdate(BaseModel):
    content: str | None = None
    content_name: str | None = None
