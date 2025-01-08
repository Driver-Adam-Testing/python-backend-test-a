from uuid import UUID

from database.models_v2 import (
    Node,
    PrimaryAsset,
    Version,
)
from fastapi import Body, HTTPException, Path, Request
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
