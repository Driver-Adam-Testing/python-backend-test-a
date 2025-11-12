from uuid import UUID

from database.models import Tag
from fastapi import Body, HTTPException, Path, Request
from sqlmodel import func, select

from app.api.auth import UserToken
from app.api.routes.v2.query_utils import (
    Pagination,
    apply_filters_to_query,
    apply_sorting_to_query,
)
from app.api.routes.v2.router import router
from app.api.routes.v2.schemas import ListWithCount, TagCreate, TagDetailRead, TagRead
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_org_membership


@router.get("/tags", response_model=ListWithCount[TagDetailRead])
def list_tags(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
) -> ListWithCount[TagDetailRead]:
    enforce_org_membership(session, user)
    query = select(Tag).where(Tag.organization_id == user.organization_id)

    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, Tag)
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = apply_sorting_to_query(query, pagination, Tag)
    result = session.exec(query)
    tags = result.all()

    return ListWithCount(results=tags, total_count=total_count)


@router.put("/tags/{tag_id}", response_model=TagRead)
def update_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: UUID = Path(...),
    payload: TagCreate = Body(...),
) -> TagRead:
    enforce_org_membership(session, user)
    tag = session.exec(
        select(Tag)
        .where(Tag.id == tag_id)
        .where(Tag.organization_id == user.organization_id)
    ).one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if payload.name is not None:
        tag.name = payload.name
    if payload.hex_color is not None:
        tag.hex_color = payload.hex_color
    if payload.type is not None:
        tag.type = payload.type

    tag.updated_by = user.user_id

    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.post("/tags", response_model=TagRead)
def create_tag(
    session: CurrentSession,
    user: UserToken,
    payload: TagCreate = Body(...),
) -> TagRead:
    enforce_org_membership(session, user)
    # Create a new Tag
    new_tag = Tag(
        name=payload.name,
        organization_id=user.organization_id,
        hex_color=payload.hex_color,
        type="tag",
        created_by=user.user_id,
        updated_by=user.user_id,
    )
    session.add(new_tag)
    session.commit()
    session.refresh(new_tag)
    return new_tag
