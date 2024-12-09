from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from app.api.auth import UserToken
from app.api.session import CurrentSession
from database.models_v1 import DerivedContent
from database.models_v2 import FullNodeView, NodeRow, PrimaryAssetRow, VersionRow
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
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
