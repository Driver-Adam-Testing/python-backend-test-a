from typing import Any

from database.models import DerivedContent, Node, PrimaryAsset, Version
from fastapi import Request
from shared.authorization.query_filters import (
    content_grant_filter,
    exclude_page_assets_filter,
    page_content_grant_filter,
)
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

    This endpoint filters content based on the user's grants to the associated PrimaryAsset.
    Users will only see content from PrimaryAssets they have access to via:
    - Direct user grants
    - Team membership grants
    - Organization-wide grants
    - Public grants

    NOTE: This endpoint excludes page-related assets. Use /page_contents for page content.
    """
    return _list_contents_with_filter(
        request,
        session,
        user,
        pagination,
        include_content,
        auth_filter=lambda s, uid, oid: content_grant_filter(s, uid, oid),
        additional_filters=[_exclude_page_content()],
    )


@router.get("/page_contents")
def list_page_contents(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    include_content: bool = False,
) -> ListWithCount[ContentDetailReadSkinny] | ListWithCount[ContentDetailRead]:
    """
    List contents from page assets with source-based authorization.

    By default returns skinny response without content field for efficiency.

    This endpoint only returns content from PAGE and PAGE_TEMPLATE assets.
    Authorization is source-based: user must have access to ALL sources
    referenced by each page to see its content.
    """
    return _list_contents_with_filter(
        request,
        session,
        user,
        pagination,
        include_content,
        auth_filter=lambda s, uid, oid: page_content_grant_filter(s, uid, oid),
        additional_filters=[],
    )


def _list_contents_with_filter(
    request: Request,
    session: CurrentSession,
    user: User,
    pagination: Pagination,
    include_content: bool,
    auth_filter: callable,
    additional_filters: list[Any],
) -> ListWithCount[ContentDetailReadSkinny] | ListWithCount[ContentDetailRead]:
    query = (
        select(DerivedContent)
        .options(
            selectinload(DerivedContent.node)
            .selectinload(Node.version)
            .selectinload(Version.primary_asset)
            .selectinload(PrimaryAsset.tags)
        )
        .where(_org_filter(user.organization_id))
    )

    for filter_condition in additional_filters:
        query = query.where(filter_condition)

    query = query.where(auth_filter(session, user.user_id, user.organization_id))

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


def _exclude_page_content() -> Any:
    return DerivedContent.node.has(
        Node.version.has(Version.primary_asset.has(exclude_page_assets_filter()))
    )


def _org_filter(organization_id: str) -> Any:
    return DerivedContent.node.has(
        Node.version.has(
            Version.primary_asset.has(PrimaryAsset.organization_id == organization_id)
        )
    )
