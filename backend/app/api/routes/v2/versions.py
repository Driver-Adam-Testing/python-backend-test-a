from uuid import UUID

from database.models import PrimaryAsset, Version
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
    VersionDetailRead,
    VersionUpdate,
)
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action


@router.get("/versions", response_model=ListWithCount[VersionDetailRead])
def list_versions(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
) -> ListWithCount[VersionDetailRead]:
    # TODO: authorization with list endpoint
    query = (
        select(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
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


@router.put("/versions/{version_id}", response_model=Version)
def update_version(
    session: CurrentSession,
    user: UserToken,
    version_id: UUID = Path(...),
    payload: VersionUpdate = Body(...),
) -> Version:
    version = session.exec(
        select(Version)
        .join(PrimaryAsset)
        .where(Version.id == version_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()
    enforce_asset_action(
        db=session,
        user=user,
        asset_id=version.primary_asset_id,
        action_key="asset.manage",
    )

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if payload.status:
        version.status = payload.status

    session.add(version)
    session.commit()
    session.refresh(version)
    return version
