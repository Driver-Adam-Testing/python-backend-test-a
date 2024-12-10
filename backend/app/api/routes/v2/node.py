from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from app.api.auth import UserToken
from app.api.session import CurrentSession
from database.models_v1 import DerivedContent
from database.models_v2 import (
    FullNodeView,
    NodeRow,
    PrimaryAssetRow,
    PrimaryAssetTypeEnum,
    VersionRow,
)
from fastapi import APIRouter, Body, HTTPException, Path, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

T = TypeVar("T")


class ListWithCount(BaseModel, Generic[T]):
    results: list[T]
    total_count: int


router = APIRouter()


@router.get("/full_nodes", response_model=ListWithCount[FullNodeView])
async def list_full_nodes(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "primary_asset_updated_at",
    sort_direction: str = "DESC",
    root_nodes_only: bool = False,
) -> ListWithCount[FullNodeView]:
    query = select(FullNodeView).where(
        FullNodeView.primary_asset_organization_id == user.organization_id
    )

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(FullNodeView, key):
            query = query.where(getattr(FullNodeView, key) == value)

    if root_nodes_only:
        query = query.where(
            ~FullNodeView.node_relative_path.contains("/")
            | (
                FullNodeView.node_relative_path.endswith("/")
                & (
                    func.length(FullNodeView.node_relative_path)
                    - func.length(
                        func.replace(FullNodeView.node_relative_path, "/", "")
                    )
                    == 1
                )
            )
        )
    if hasattr(FullNodeView, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(FullNodeView, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(FullNodeView, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    full_nodes = result.all()

    if not full_nodes:
        raise HTTPException(status_code=404, detail="No full nodes found")

    return ListWithCount(results=full_nodes, total_count=total_count)


@router.get("/primary_assets", response_model=ListWithCount[PrimaryAssetRow])
async def list_primary_assets(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
) -> ListWithCount[PrimaryAssetRow]:
    query = select(PrimaryAssetRow).where(
        PrimaryAssetRow.organization_id == user.organization_id
    )

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(PrimaryAssetRow, key):
            query = query.where(getattr(PrimaryAssetRow, key) == value)

    if hasattr(PrimaryAssetRow, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(PrimaryAssetRow, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(PrimaryAssetRow, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    primary_assets = result.all()

    return ListWithCount(results=primary_assets, total_count=total_count)


@router.get("/versions", response_model=ListWithCount[VersionRow])
async def list_versions(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
) -> ListWithCount[VersionRow]:
    query = (
        select(VersionRow)
        .join(PrimaryAssetRow)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
    )

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(VersionRow, key):
            query = query.where(getattr(VersionRow, key) == value)

    if hasattr(VersionRow, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(VersionRow, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(VersionRow, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    versions = result.all()

    if not versions:
        raise HTTPException(status_code=404, detail="No versions found")

    return ListWithCount(results=versions, total_count=total_count)


@router.get("/nodes", response_model=ListWithCount[NodeRow])
async def list_nodes(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
) -> ListWithCount[NodeRow]:
    query = (
        select(NodeRow)
        .join(VersionRow)
        .join(PrimaryAssetRow)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
        .options(selectinload(NodeRow.version))
    )

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(NodeRow, key):
            query = query.where(getattr(NodeRow, key) == value)

    if hasattr(NodeRow, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(NodeRow, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(NodeRow, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    nodes = result.all()

    if not nodes:
        raise HTTPException(status_code=404, detail="No nodes found")

    return ListWithCount(results=nodes, total_count=total_count)


class DerivedContentResponse(BaseModel):
    id: UUID | None
    content_type_id: UUID
    source_content_id: UUID | None
    node_id: UUID | None
    relative_path: str
    content: str | None
    content_name: str | None
    misc_metadata: dict | None
    status: str | None
    created_at: datetime | None
    updated_at: datetime | None
    order: int | None
    version_id: UUID | None
    tags: list[dict] = []  # Include entire tag objects
    full_node: dict | None = None  # Include full node details

    @classmethod
    def from_derived_content(
        cls, derived_content: DerivedContent
    ) -> "DerivedContentResponse":
        return cls(
            id=derived_content.id,
            content_type_id=derived_content.content_type_id,
            source_content_id=derived_content.source_content_id,
            node_id=derived_content.node_id,
            relative_path=derived_content.relative_path,
            content=derived_content.content,
            content_name=derived_content.content_name,
            misc_metadata=derived_content.misc_metadata,
            status=derived_content.status.value if derived_content.status else None,
            created_at=derived_content.created_at,
            updated_at=derived_content.updated_at,
            order=derived_content.order,
            version_id=derived_content.version_id,
            tags=[
                {"id": tag.id, "name": tag.name} for tag in derived_content.tags
            ],  # Extract entire tag objects
            full_node={
                "primary_asset_id": derived_content.full_node.primary_asset_id,
                "primary_asset_display_name": derived_content.full_node.primary_asset_display_name,
                "primary_asset_organization_id": derived_content.full_node.primary_asset_organization_id,
                "version_id": derived_content.full_node.version_id,
                "version_display_name": derived_content.full_node.version_display_name,
                "node_id": derived_content.full_node.node_id,
                "node_relative_path": derived_content.full_node.node_relative_path,
            }
            if derived_content.full_node
            else None,  # Extract full node details
        )


@router.get("/contents", response_model=ListWithCount[DerivedContentResponse])
async def list_contents(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
    content_type_names: str | list[str] = "",
) -> ListWithCount[DerivedContentResponse]:
    query = (
        select(DerivedContent)
        .select_from(DerivedContent)
        .join(FullNodeView, DerivedContent.node_id == FullNodeView.node_id)
        .where(FullNodeView.primary_asset_organization_id == user.organization_id)
    )

    if content_type_names:
        if isinstance(content_type_names, str):
            content_type_names = [content_type_names]
        query = query.where(DerivedContent.content_type_slug.in_(content_type_names))

    filters = dict(request.query_params)
    filters.pop("limit", None)
    filters.pop("offset", None)
    filters.pop("sort_by", None)
    filters.pop("sort_direction", None)

    for key, value in filters.items():
        if hasattr(DerivedContent, key):
            query = query.where(getattr(DerivedContent, key) == value)
        elif key.startswith("full_node_") and hasattr(FullNodeView, key[10:]):
            query = query.where(getattr(FullNodeView, key[10:]) == value)

    if hasattr(DerivedContent, sort_by):
        if sort_direction.upper() == "ASC":
            query = query.order_by(getattr(DerivedContent, sort_by).asc())
        elif sort_direction.upper() == "DESC":
            query = query.order_by(getattr(DerivedContent, sort_by).desc())
        else:
            raise HTTPException(status_code=400, detail="Invalid sort direction")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.limit(limit).offset(offset)
    result = session.exec(query)
    contents_with_full_node = result.all()

    if not contents_with_full_node:
        raise HTTPException(status_code=404, detail="No contents found")

    # Use DerivedContentResponse to populate the response
    contents = [
        DerivedContentResponse.from_derived_content(derived_content)
        for derived_content in contents_with_full_node
    ]

    return ListWithCount(results=contents, total_count=total_count)


class PrimaryAssetCreate(BaseModel):
    display_name: str
    primary_asset_type: str

    @field_validator("primary_asset_type")
    def validate_primary_asset_type(cls, v: str) -> str:
        if v not in [e.value for e in PrimaryAssetTypeEnum]:
            raise ValueError(
                f"primary_asset_type must be one of {[e.value for e in PrimaryAssetTypeEnum]}"
            )
        return v


class PrimaryAssetUpdate(BaseModel):
    display_name: str | None = None
    primary_asset_type: str | None = None

    @field_validator("primary_asset_type")
    def validate_primary_asset_type(cls, v: str | None) -> str | None:
        if v is not None and v not in [e.value for e in PrimaryAssetTypeEnum]:
            raise ValueError(
                f"primary_asset_type must be one of {[e.value for e in PrimaryAssetTypeEnum]}"
            )
        return v


@router.post("/primary_assets", response_model=PrimaryAssetRow)
async def create_primary_asset(
    session: CurrentSession,
    user: UserToken,
    payload: PrimaryAssetCreate = Body(...),
) -> PrimaryAssetRow:
    # Create a new PrimaryAssetRow
    new_asset = PrimaryAssetRow(
        display_name=payload.display_name,
        organization_id=user.organization_id,
        primary_asset_type=payload.primary_asset_type,
    )
    session.add(new_asset)
    session.commit()
    session.refresh(new_asset)
    return new_asset


@router.put("/primary_assets/{asset_id}", response_model=PrimaryAssetRow)
async def update_primary_asset(
    session: CurrentSession,
    user: UserToken,
    asset_id: UUID = Path(...),
    payload: PrimaryAssetUpdate = Body(...),
) -> PrimaryAssetRow:
    # Fetch the asset to be updated
    asset = session.exec(
        select(PrimaryAssetRow)
        .where(PrimaryAssetRow.id == asset_id)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
    ).one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Primary asset not found")

    # Update fields if provided
    if payload.display_name is not None:
        asset.display_name = payload.display_name
    if payload.primary_asset_type is not None:
        if payload.primary_asset_type not in [e.value for e in PrimaryAssetTypeEnum]:
            raise HTTPException(status_code=400, detail="Invalid primary_asset_type")
        asset.primary_asset_type = payload.primary_asset_type

    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


class VersionCreate(BaseModel):
    primary_asset_id: UUID
    display_name: str


class VersionUpdate(BaseModel):
    display_name: str | None = None


@router.post("/versions", response_model=VersionRow)
async def create_version(
    session: CurrentSession,
    user: UserToken,
    payload: VersionCreate = Body(...),
) -> VersionRow:
    # Ensure that the primary asset belongs to the user's organization
    primary_asset = session.exec(
        select(PrimaryAssetRow)
        .where(PrimaryAssetRow.id == payload.primary_asset_id)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
    ).one_or_none()

    if not primary_asset:
        raise HTTPException(status_code=404, detail="Primary asset not found")

    new_version = VersionRow(
        primary_asset_id=payload.primary_asset_id,
        display_name=payload.display_name,
    )
    session.add(new_version)
    session.commit()
    session.refresh(new_version)
    return new_version


@router.put("/versions/{version_id}", response_model=VersionRow)
async def update_version(
    session: CurrentSession,
    user: UserToken,
    version_id: UUID = Path(...),
    payload: VersionUpdate = Body(...),
) -> VersionRow:
    version = session.exec(
        select(VersionRow)
        .join(PrimaryAssetRow)
        .where(VersionRow.id == version_id)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
    ).one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if payload.display_name is not None:
        version.display_name = payload.display_name

    session.add(version)
    session.commit()
    session.refresh(version)
    return version


class NodeCreate(BaseModel):
    version_id: UUID
    relative_path: str


class NodeUpdate(BaseModel):
    relative_path: str | None = None


@router.post("/nodes", response_model=NodeRow)
async def create_node(
    session: CurrentSession, user: UserToken, payload: NodeCreate = Body(...)
) -> NodeRow:
    # Verify version belongs to user's organization
    version = session.exec(
        select(VersionRow)
        .join(PrimaryAssetRow)
        .where(VersionRow.id == payload.version_id)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
    ).one_or_none()

    if not version:
        raise HTTPException(
            status_code=404, detail="Version not found or not authorized"
        )

    new_node = NodeRow(
        version_id=payload.version_id,
        relative_path=payload.relative_path,
    )
    session.add(new_node)
    session.commit()
    session.refresh(new_node)
    return new_node


@router.put("/nodes/{node_id}", response_model=NodeRow)
async def update_node(
    session: CurrentSession,
    user: UserToken,
    node_id: UUID = Path(...),
    payload: NodeUpdate = Body(...),
) -> NodeRow:
    # Fetch the node and ensure it belongs to the user's organization
    node = session.exec(
        select(NodeRow)
        .join(VersionRow)
        .join(PrimaryAssetRow)
        .where(NodeRow.id == node_id)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
    ).one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found or not authorized")

    if payload.relative_path is not None:
        node.relative_path = payload.relative_path

    session.add(node)
    session.commit()
    session.refresh(node)
    return node


class DerivedContentCreate(BaseModel):
    node_id: UUID
    content_type_id: UUID
    relative_path: str
    content: str | None = None
    content_name: str | None = None
    misc_metadata: dict | None = None
    status: str | None = None
    order: int | None = None
    # For tags, you might want to create them separately or link existing tags.
    # Here we assume tags are handled elsewhere or via another endpoint.


class DerivedContentUpdate(BaseModel):
    relative_path: str | None = None
    content: str | None = None
    content_name: str | None = None
    misc_metadata: dict | None = None
    status: str | None = None
    order: int | None = None
    # Similarly, tag updates could be handled separately or by including logic here.


@router.post("/contents", response_model=DerivedContentResponse)
async def create_derived_content(
    session: CurrentSession, user: UserToken, payload: DerivedContentCreate = Body(...)
) -> DerivedContentResponse:
    # Verify node belongs to user's organization
    node = session.exec(
        select(NodeRow)
        .join(VersionRow)
        .join(PrimaryAssetRow)
        .where(NodeRow.id == payload.node_id)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
    ).one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found or not authorized")

    new_content = DerivedContent(
        node_id=payload.node_id,
        content_type_id=payload.content_type_id,
        relative_path=payload.relative_path,
        content=payload.content,
        content_name=payload.content_name,
        misc_metadata=payload.misc_metadata,
        status=payload.status,
        order=payload.order,
    )
    session.add(new_content)
    session.commit()
    session.refresh(new_content)

    return DerivedContentResponse.from_derived_content(new_content)


@router.put("/contents/{content_id}", response_model=DerivedContentResponse)
async def update_derived_content(
    session: CurrentSession,
    user: UserToken,
    content_id: UUID = Path(...),
    payload: DerivedContentUpdate = Body(...),
) -> DerivedContentResponse:
    # Fetch the derived content and ensure it belongs to the user's organization
    derived_content = session.exec(
        select(DerivedContent)
        .join(NodeRow)
        .join(VersionRow)
        .join(PrimaryAssetRow)
        .where(DerivedContent.id == content_id)
        .where(PrimaryAssetRow.organization_id == user.organization_id)
    ).one_or_none()

    if not derived_content:
        raise HTTPException(
            status_code=404, detail="Content not found or not authorized"
        )

    if payload.relative_path is not None:
        derived_content.relative_path = payload.relative_path
    if payload.content is not None:
        derived_content.content = payload.content
    if payload.content_name is not None:
        derived_content.content_name = payload.content_name
    if payload.misc_metadata is not None:
        derived_content.misc_metadata = payload.misc_metadata
    if payload.status is not None:
        derived_content.status = payload.status
    if payload.order is not None:
        derived_content.order = payload.order

    session.add(derived_content)
    session.commit()
    session.refresh(derived_content)

    return DerivedContentResponse.from_derived_content(derived_content)
