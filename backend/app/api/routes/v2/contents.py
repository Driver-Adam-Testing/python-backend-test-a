from database.models_v1 import DerivedContent
from database.models_v2 import Node, PrimaryAsset, Version
from fastapi import Body, HTTPException, Request
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
    ContentCreate,
    ContentDetailRead,
    ListWithCount,
)
from app.api.session import CurrentSession
from app.auth.models import User


@router.get("/contents", response_model=ListWithCount[ContentDetailRead])
def list_contents(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
) -> ListWithCount[ContentDetailRead]:
    return _list_contents(request, session, user, pagination)


def _list_contents(
    request: Request,
    session: CurrentSession,
    user: User,
    pagination: Pagination,
) -> ListWithCount[ContentDetailRead]:
    query = (
        select(DerivedContent)
        .options(
            selectinload(DerivedContent.node)
            .selectinload(Node.version)
            .selectinload(Version.primary_asset)
            .selectinload(PrimaryAsset.tags)
        )
        .where(
            DerivedContent.node.has(
                Node.version.has(
                    Version.primary_asset.has(
                        PrimaryAsset.organization_id == user.organization_id
                    )
                )
            )
        )
    )

    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, DerivedContent)
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = apply_sorting_to_query(query, pagination, DerivedContent)
    result = session.exec(query)
    contents = result.all()

    return ListWithCount(results=contents, total_count=total_count)


@router.post("/contents", response_model=ContentDetailRead)
def create_derived_content(
    session: CurrentSession, user: UserToken, payload: ContentCreate = Body(...)
) -> ContentDetailRead:
    # Verify node belongs to user's organization
    node = session.exec(
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(Node.id == payload.node_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found or not authorized")

    new_content = DerivedContent(
        node_id=payload.node_id,
        relative_path=payload.relative_path,
        content=payload.content,
        content_name=payload.content_name,
        misc_metadata=payload.misc_metadata,
        order=payload.order,
    )
    session.add(new_content)
    session.commit()
    session.refresh(new_content)

    return new_content
