# node_schemas.py
from datetime import datetime
from uuid import UUID

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

    class Config:
        orm_mode = True


class PrimaryAssetRead(BaseModel):
    id: UUID
    organization_id: str
    primary_asset_type: str
    display_name: str
    created_at: datetime | None
    updated_at: datetime | None
    versions: list[VersionRead] | None = None

    class Config:
        orm_mode = True


# Create and Update Schemas


class PrimaryAssetCreate(BaseModel):
    display_name: str
    primary_asset_type: str


class PrimaryAssetUpdate(BaseModel):
    display_name: str | None = None
    primary_asset_type: str | None = None


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
