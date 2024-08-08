import logging

from database.models_v1 import Tag
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.auth import CurrentUser
from app.api.content.content import ListContentInput, ListContentResult, list_content

logger = logging.getLogger(__name__)


class ListTagsInput(BaseModel):
    name: str | None
    limit: int
    offset: int


class NewTagInput(BaseModel):
    name: str
    hexColor: str


class ListTagsResults(BaseModel):
    results: list[Tag]
    offset: int
    limit: int
    count: int


class ListTagContentsResults(BaseModel):
    tag: Tag
    results: list[ListContentResult]
    offset: int
    limit: int
    count: int


def list_tags(
    session: Session, user: CurrentUser, input: ListTagsInput
) -> ListTagsResults:
    statement = select(Tag).where(user.organization_id == Tag.organization_id)
    count_statement = (
        select(func.count())
        .select_from(Tag)
        .where(user.organization_id == Tag.organization_id)
    )

    if input.name:
        statement = statement.where(Tag.name.contains(input.name))
        count_statement = count_statement.where(Tag.name.contains(input.name))

    total_count = session.exec(count_statement).one()
    results = session.exec(statement.offset(input.offset).limit(input.limit)).all()
    return ListTagsResults(
        results=results, offset=input.offset, limit=input.limit, count=total_count
    )


def create_tag(session: Session, user: CurrentUser, input: NewTagInput) -> Tag:
    tag = Tag(
        name=input.name.strip(),
        hex_color=input.hexColor.strip(),
        organization_id=user.organization_id,
        created_by=user.user_id,
        updated_by=user.user_id,
    )
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


def edit_tag(
    session: Session, user: CurrentUser, tag_id: int, input: NewTagInput
) -> Tag:
    tag = session.exec(
        select(Tag).where(
            Tag.id == tag_id and Tag.organization_id == user.organization_id
        )
    ).first()
    if tag:
        tag.name = input.name.strip()
        tag.hex_color = input.hexColor.strip()
        tag.updated_by = user.user_id
        session.commit()
        session.refresh(tag)
        return tag
    logger.error("Tag not found to edit")
    raise HTTPException(status_code=404, detail="Tag not found")


def list_tag_contents(
    session: Session, user: CurrentUser, tag_id: str, input: ListContentInput
) -> ListTagContentsResults:
    tag = session.exec(
        select(Tag).where(
            Tag.id == tag_id and Tag.organization_id == user.organization_id
        )
    ).first()
    if tag:
        content = list_content(
            session,
            user,
            input=ListContentInput(
                limit=input.limit,
                offset=input.offset,
                text=input.text,
                content_type_id=input.content_type_id,
                content_type_name=input.content_type_name,
                sort_by=input.sort_by,
                sort_direction=input.sort_direction,
                status=input.status,
                tag_ids=[tag_id],
            ),
        )
        return ListTagContentsResults(
            tag=tag,
            results=content.results,
            offset=input.offset,
            limit=input.limit,
            count=content.count,
        )
    logger.error("Tag not found.")
    raise HTTPException(status_code=404, detail="Tag not found")
