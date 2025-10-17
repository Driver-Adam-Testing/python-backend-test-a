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
from app.authorization.query_filters import content_grant_filter


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
    """
    return _list_contents(request, session, user, pagination, include_content)


def _list_contents(
    request: Request,
    session: CurrentSession,
    user: User,
    pagination: Pagination,
    include_content: bool = False,
) -> ListWithCount[ContentDetailReadSkinny] | ListWithCount[ContentDetailRead]:
    query = _base_content_query(session, user.user_id, user.organization_id)

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


def _base_content_query(
    session: CurrentSession, user_id: str, organization_id: str
) -> Any:
    """
    Build base query for contents with authorization filtering.

    Only returns content where the user has access to the associated PrimaryAsset
    through grants (user, team, org, or public).
    """
    return (
        select(DerivedContent)
        .options(
            selectinload(DerivedContent.node)
            .selectinload(Node.version)
            .selectinload(Version.primary_asset)
            .selectinload(PrimaryAsset.tags)
        )
        .where(_org_filter(organization_id))
        .where(content_grant_filter(session, user_id, organization_id))
    )


def _org_filter(organization_id: str) -> Any:
    return DerivedContent.node.has(
        Node.version.has(
            Version.primary_asset.has(PrimaryAsset.organization_id == organization_id)
        )
    )
