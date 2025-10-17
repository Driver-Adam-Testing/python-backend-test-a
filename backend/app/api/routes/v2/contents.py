from typing import Any

from database.models import DerivedContent, Node, PrimaryAsset, Version
from fastapi import Request
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
    ContentDetailRead,
    ContentDetailReadSkinny,
    ListWithCount,
)
from app.api.session import CurrentSession
from app.auth.models import User


@router.get("/contents")
def list_contents(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    include_content: bool = False,
) -> ListWithCount[ContentDetailReadSkinny] | ListWithCount[ContentDetailRead]:
    """
    List contents with optional content field loading.

    By default returns skinny response without content field for efficiency.

    TODO: Add organization_id to DerivedContent model to eliminate joins.
    """
    return _list_contents(request, session, user, pagination, include_content)


def _list_contents(
    request: Request,
    session: CurrentSession,
    user: User,
    pagination: Pagination,
    include_content: bool = False,
) -> ListWithCount[ContentDetailReadSkinny] | ListWithCount[ContentDetailRead]:
    query = _base_content_query(user.organization_id)

    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, DerivedContent)
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = apply_sorting_to_query(query, pagination, DerivedContent)
    result = session.exec(query)
    contents = result.all()

    if include_content:
        return ListWithCount[ContentDetailRead](
            results=contents, total_count=total_count
        )
    else:
        return ListWithCount[ContentDetailReadSkinny](
            results=contents, total_count=total_count
        )


def _base_content_query(organization_id: str) -> Any:
    return (
        select(DerivedContent)
        .options(
            selectinload(DerivedContent.node)
            .selectinload(Node.version)
            .selectinload(Version.primary_asset)
            .selectinload(PrimaryAsset.tags)
        )
        .where(_org_filter(organization_id))
    )


def _org_filter(organization_id: str) -> Any:
    return DerivedContent.node.has(
        Node.version.has(
            Version.primary_asset.has(PrimaryAsset.organization_id == organization_id)
        )
    )
