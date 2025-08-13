# node_schemas.py
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from database.models_v2_enums import (
    ContentKind,
    NodeKind,
    PrimaryAssetKind,
    VcsAutoUpdatePolicy,
    VersionStatus,
)
from pydantic import BaseModel, computed_field

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
    repository_id: str | None

    class Config:
        from_attributes = True


class VersionRead(BaseModel):
    id: UUID
    primary_asset_id: UUID
    vcs_hash: str | None
    created_at: datetime | None
    updated_at: datetime | None
    status: str | None
    browsable: bool
    vcs_metadata: dict | None

    class Config:
        from_attributes = True


class NodeRead(BaseModel):
    id: UUID
    version_id: UUID
    relative_path: str
    kind: NodeKind
    created_at: datetime | None
    updated_at: datetime | None
    depth: int

    class Config:
        from_attributes = True


class UserRead(BaseModel):
    id: str
    full_name: str
    email: str

    class Config:
        from_attributes = True


class NodeMetaReadWithTerseSentence(NodeRead):
    # NOTE: this is only used on the list_primary_assets endpoint
    # With that endpoint, we want the terse sentence description
    # DO NOT use this schema elsewhere without appropriate filters, otherwise it will
    # load all contents for every node pulled.
    id: UUID
    version_id: UUID
    relative_path: str
    kind: NodeKind
    created_at: datetime | None
    updated_at: datetime | None
    misc_metadata: dict | None
    total_files: int | None
    depth: int
    contents: list["ContentRead"] | None

    class Config:
        from_attributes = True


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
        from_attributes = True


class PrimaryAssetTagRead(BaseModel):
    tag_id: UUID
    primary_asset_id: UUID

    class Config:
        from_attributes = True


class ContentRead(BaseModel):
    id: UUID | None
    node_id: UUID | None
    content: str | None
    content_kind: ContentKind
    misc_metadata: dict | None
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class DocumentSourceRead(BaseModel):
    page_node_id: UUID | None
    source_node_id: UUID | None

    class Config:
        from_attributes = True


#######################
# DETAIL READ SCHEMAS #
#######################


class NodeDetailRead(NodeRead):
    class NodeVersionRead(VersionRead):
        primary_asset: PrimaryAssetRead
        creator: UserRead | None

    version: NodeVersionRead

    class Config:
        from_attributes = True


class VersionDetailRead(VersionRead):
    primary_asset: PrimaryAssetRead
    root_node: NodeRead | None
    creator: UserRead | None

    class Config:
        from_attributes = True


class PrimaryAssetDetailRead(PrimaryAssetRead):
    # NOTE: this is only used for the list_primary_assets endpoint right now.
    # It includes the most recent version and its root node with terse sentence by
    # including the contents on NodeMetaReadWithTerseSentence.
    # Do NOT use the schema elsewhere without appropriate filters, or it will fetch all contents
    # for every node pulled.
    class PrimaryAssetVersionRead(VersionRead):
        root_node: NodeMetaReadWithTerseSentence | None
        creator: UserRead | None

    most_recent_version: PrimaryAssetVersionRead | None
    tags: list[TagRead] | None
    codebase_settings_auto_commit_docs: bool | None = None

    @computed_field
    @property
    def browsable(self) -> bool:
        """A primary asset is browsable if any of its versions are browsable."""
        return self.most_recent_version.browsable if self.most_recent_version else False

    class Config:
        from_attributes = True


class PrimaryAssetTagDetailRead(PrimaryAssetTagRead):
    primary_asset: PrimaryAssetRead


class ContentDetailRead(ContentRead):
    node: NodeDetailRead

    class Config:
        from_attributes = True


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
    codebase_settings_auto_commit_docs: bool | None = None
    auto_update_policy: VcsAutoUpdatePolicy | None


class VersionUpdate(BaseModel):
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


class ContentCreate(BaseModel):
    node_id: UUID
    content_kind: ContentKind
    content: str | None = None
    misc_metadata: dict | None = None


class DerivedContentUpdate(BaseModel):
    content: str | None = None
    content_name: str | None = None


class DocumentSourceCreate(BaseModel):
    source_node_id: UUID
    page_node_id: UUID


class PrimaryAssetTagCreate(BaseModel):
    tag_id: UUID
    primary_asset_id: UUID
