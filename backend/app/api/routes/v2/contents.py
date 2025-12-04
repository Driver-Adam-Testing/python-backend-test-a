from typing import Any
from uuid import UUID

from database.models import DerivedContent, Node, PrimaryAsset, Version, VersionNode
from fastapi import HTTPException, Request
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
from app.api.routes.v2.schemas import ContentsResponse, ListWithCount
from app.api.session import CurrentSession
from app.auth.models import User


@router.get("/contents")
def list_contents(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    version_node_id: UUID,
    include_content: bool = False,
) -> ListWithCount[ContentsResponse]:
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
        version_node_id,
        auth_filter=lambda s, uid, oid: content_grant_filter(s, uid, oid),
        additional_filters=[_exclude_page_content()],
    )


def _list_contents_with_filter(
    request: Request,
    session: CurrentSession,
    user: User,
    pagination: Pagination,
    include_content: bool,
    version_node_id: UUID,
    auth_filter: callable,
    additional_filters: list[Any],
) -> ListWithCount[ContentsResponse]:
    query = (
        select(DerivedContent)
        .join(DerivedContent.node)
        .join(Node.version_nodes)
        .options(
            selectinload(DerivedContent.node)
            .selectinload(Node.version_nodes)
            .selectinload(VersionNode.version)
            .selectinload(Version.primary_asset),
        )
        .where(VersionNode.id == version_node_id)
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
    contents: list[DerivedContent] = session.exec(query).all()

    results = [
        ContentsResponse(
            version_node_id=content.node.version_nodes[0].id,
            content_id=content.id,
            content=content.content if include_content else None,
            content_name=content.content_name,
            content_kind=content.content_kind,
            version_status=content.node.version_nodes[0].version.status,
            primary_asset_display_name=content.node.version_nodes[
                0
            ].version.primary_asset.display_name,
            misc_metadata=content.node.version_nodes[0].misc_metadata,
            created_at=content.created_at,
            updated_at=content.updated_at,
        )
        for content in contents
    ]

    return ListWithCount[ContentsResponse](results=results, total_count=total_count)


@router.get("/page_contents")
def list_page_contents(
    session: CurrentSession,
    user: UserToken,
    page_version_node_id: UUID,
    include_content: bool = False,
) -> ContentsResponse:
    """
    Get contents for a specific page version node.

    By default returns response without content field for efficiency.

    This endpoint returns content from PAGE and PAGE_TEMPLATE assets.
    Authorization is source-based: user must have access to ALL sources
    referenced by the page to see its content.
    """
    return _get_page_content(
        session,
        user,
        page_version_node_id,
        include_content,
    )


def _get_page_content(
    session: CurrentSession,
    user: User,
    page_version_node_id: UUID,
    include_content: bool,
) -> ContentsResponse:
    query = (
        select(VersionNode)
        .join(VersionNode.node)
        .options(selectinload(VersionNode.version).selectinload(Version.primary_asset))
        .options(selectinload(VersionNode.node).selectinload(Node.contents))
        .where(VersionNode.id == page_version_node_id)
        .where(_org_filter(user.organization_id))
    )

    query = query.where(
        page_content_grant_filter(session, user.user_id, user.organization_id)
    )

    version_node = session.exec(query).one_or_none()

    if not version_node:
        raise HTTPException(status_code=404, detail="Version node not found")

    derived_content = version_node.node.contents[0]

    return ContentsResponse(
        version_node_id=version_node.id,
        content=derived_content.content if include_content else None,
        content_id=derived_content.id,
        content_name=derived_content.content_name,
        content_kind=derived_content.content_kind,
        version_status=version_node.version.status,
        primary_asset_display_name=version_node.version.primary_asset.display_name,
        misc_metadata=version_node.misc_metadata,
        created_at=derived_content.created_at,
        updated_at=derived_content.updated_at,
    )


def _exclude_page_content() -> Any:
    return DerivedContent.node.has(
        Node.version_nodes.any(
            VersionNode.version.has(
                Version.primary_asset.has(exclude_page_assets_filter())
            )
        )
    )


def _org_filter(organization_id: str) -> Any:
    return VersionNode.version.has(
        Version.primary_asset.has(PrimaryAsset.organization_id == organization_id)
    )
