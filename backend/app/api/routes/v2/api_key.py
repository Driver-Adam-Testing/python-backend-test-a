from uuid import UUID

from database.models import ApiKey
from fastapi import APIRouter, HTTPException, Path, Request
from sqlmodel import func, select

from app.api.auth import UserToken
from app.api.routes.v2.query_utils import (
    Pagination,
    apply_filters_to_query,
    apply_sorting_to_query,
)
from app.api.routes.v2.schemas import ListWithCount
from app.api.session import CurrentSession

router = APIRouter()


@router.post("/", response_model=ApiKey)
def create_api_key(
    session: CurrentSession,
    user: UserToken,
) -> ApiKey:
    api_key = ApiKey(
        organization_id=user.organization_id,
        user_id=user.user_id,
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return api_key


@router.get("/", response_model=ListWithCount[ApiKey])
def get_api_keys(
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    request: Request,
) -> ListWithCount[ApiKey]:
    query = (
        select(ApiKey)
        .where(ApiKey.user_id == user.user_id)
        .where(ApiKey.organization_id == user.organization_id)
    )
    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, ApiKey)
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    query = apply_sorting_to_query(query, pagination, ApiKey)
    api_keys = session.exec(query).all()
    for api_key in api_keys:
        api_key.key = f"drv-{'.' *3}{api_key.key[-3:]}"
    return ListWithCount(
        results=api_keys,
        total_count=total_count,
    )


@router.delete("/{api_key_id}", response_model=None)
def delete_api_key(
    session: CurrentSession,
    user: UserToken,
    api_key_id: UUID = Path(...),
) -> None:
    api_key = session.exec(
        select(ApiKey)
        .where(ApiKey.id == api_key_id)
        .where(ApiKey.user_id == user.user_id)
        .where(ApiKey.organization_id == user.organization_id)
    ).one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    session.delete(api_key)
    session.commit()
    return None
