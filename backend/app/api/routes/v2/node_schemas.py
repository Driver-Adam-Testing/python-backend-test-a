# node_schemas.py
from datetime import datetime
from uuid import UUID

from database.models_v2_enums import PrimaryAssetKind, VersionStatus
from pydantic import BaseModel

# Read Schemas


class NodeRead(BaseModel):
    id: UUID
    version_id: UUID
    relative_path: str
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        orm_mode = True


class NodeReadWithRelationships(NodeRead):
    parent_node: NodeRead | None
    # child_nodes: list[NodeRead] | None


class VersionRead(BaseModel):
    id: UUID
    primary_asset_id: UUID
    display_name: str
    created_at: datetime | None
    updated_at: datetime | None
    root_node: NodeRead | None
    status: str | None

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


class PrimaryAssetRead(BaseModel):
    id: UUID
    organization_id: str
    kind: str
    display_name: str
    created_at: datetime | None
    updated_at: datetime | None
    versions: list[VersionRead] | None = None
    tags: list[TagRead] | None = None

    class Config:
        orm_mode = True


# Create and Update Schemas


class PrimaryAssetCreate(BaseModel):
    display_name: str
    kind: PrimaryAssetKind


class PrimaryAssetUpdate(BaseModel):
    display_name: str | None = None
    kind: PrimaryAssetKind | None = None


class VersionCreate(BaseModel):
    display_name: str
    status: VersionStatus


class VersionUpdate(BaseModel):
    display_name: str | None = None
    status: VersionStatus | None = None


class NodeCreate(BaseModel):
    version_id: UUID
    relative_path: str


class NodeUpdate(BaseModel):
    relative_path: str | None = None


class TagCreate(BaseModel):
    name: str
    hex_color: str
    type: str

    class Config:
        orm_mode = True
