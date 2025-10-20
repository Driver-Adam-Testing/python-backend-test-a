from database.models import PrimaryAsset, Version
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
    ListWithCount,
    VersionDetailRead,
)
from app.api.session import CurrentSession
from app.authorization.query_filters import primary_asset_grant_filter


@router.get("/versions", response_model=ListWithCount[VersionDetailRead])
def list_versions(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
) -> ListWithCount[VersionDetailRead]:
    query = (
        select(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
        .where(primary_asset_grant_filter(session, user.user_id, user.organization_id))
        .options(
            selectinload(Version.root_node),
            selectinload(Version.primary_asset),
            selectinload(Version.creator),
        )
    )

    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, Version)
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = apply_sorting_to_query(query, pagination, Version)
    result = session.exec(query)
    versions = result.all()

    return ListWithCount(results=versions, total_count=total_count)
