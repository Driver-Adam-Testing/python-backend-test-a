from uuid import UUID

from database.models_v2 import (
    Node,
    PrimaryAsset,
    PrimaryAssetTag,
    Version,
)
from fastapi import Body, HTTPException, Path, Request, Response
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.api.auth import UserToken
from app.api.routes.v2.query_utils import (
    Pagination,
    apply_filters_to_query,
    apply_sorting_to_query,
)
from app.api.routes.v2.router import router
from app.api.routes.v2.schemas import (
    ListWithCount,
    NodeCreate,
    NodeDetailRead,
    NodeUpdate,
)
from app.api.session import CurrentSession


@router.get("/nodes", response_model=ListWithCount[NodeDetailRead])
def list_nodes(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
) -> ListWithCount[Node]:
    query = (
        select(Node)
        .options(selectinload(Node.version).selectinload(Version.primary_asset))
        .join(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
    )

    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, Node)
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = apply_sorting_to_query(query, pagination, Node)
    result = session.exec(query)
    nodes = result.all()
    return ListWithCount(results=nodes, total_count=total_count)


@router.post("/nodes", response_model=Node)
def create_node(
    session: CurrentSession, user: UserToken, payload: NodeCreate = Body(...)
) -> Node:
    # Verify version belongs to user's organization
    version = session.exec(
        select(Version)
        .join(PrimaryAsset)
        .where(Version.id == payload.version_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not version:
        raise HTTPException(
            status_code=404, detail="Version not found or not authorized"
        )

    new_node = Node(
        version_id=payload.version_id,
        relative_path=payload.relative_path,
    )
    session.add(new_node)
    session.commit()
    session.refresh(new_node)
    return new_node


@router.put("/nodes/{node_id}", response_model=Node)
def update_node(
    session: CurrentSession,
    user: UserToken,
    node_id: UUID = Path(...),
    payload: NodeUpdate = Body(...),
) -> Node:
    # Fetch the node and ensure it belongs to the user's organization
    node = session.exec(
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(Node.id == node_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found or not authorized")

    if payload.relative_path is not None:
        node.relative_path = payload.relative_path

    session.add(node)
    session.commit()
    session.refresh(node)
    return node

    # For tags, you might want to create them separately or link existing tags.
    # Here we assume tags are handled elsewhere or via another endpoint.


# TODO: I want this to be explicitly operating on a CONCEPTUAL entity of a PAGE, rather than an explicit entity in the DB


@router.post("/primary_asset_tags", response_model=PrimaryAssetTag)
def create_primary_asset_tag(
    session: CurrentSession,
    user: UserToken,
    payload: PrimaryAssetTag = Body(...),
) -> PrimaryAssetTag:
    new_primary_asset_tag = PrimaryAssetTag(
        tag_id=payload.tag_id,
        primary_asset_id=payload.primary_asset_id,
    )
    session.add(new_primary_asset_tag)
    session.commit()
    session.refresh(new_primary_asset_tag)
    return new_primary_asset_tag


@router.delete("/primary_asset_tags/{primary_asset_id}/{tag_id}", response_model=None)
def delete_primary_asset_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: UUID = Path(...),
    primary_asset_id: UUID = Path(...),
) -> Response:
    primary_asset_tag = session.exec(
        select(PrimaryAssetTag)
        .join(PrimaryAsset)
        .where(PrimaryAssetTag.tag_id == tag_id)
        .where(PrimaryAssetTag.primary_asset_id == primary_asset_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not primary_asset_tag:
        raise HTTPException(
            status_code=404, detail="PrimaryAssetTag not found or not authorized"
        )

    session.delete(primary_asset_tag)
    session.commit()
    return Response(status_code=204)
