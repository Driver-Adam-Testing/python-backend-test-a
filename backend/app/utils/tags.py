from database.models_v1 import DerivedContent, Tag, TagContent
from pydantic import BaseModel
from sqlalchemy import and_
from sqlmodel import Session, select

from app.api.auth import CurrentUser


class ListTagsInput(BaseModel):
    name: str | None
    user_id: str | None
    limit: int
    offset: int


class NewTagInput(BaseModel):
    name: str
    hexColor: str


class ListTagsResults(BaseModel):
    results: list[Tag]
    offset: int
    limit: int


class ListTagContentsResults(BaseModel):
    tag: Tag
    content_type_ids: list[str]
    results: list[DerivedContent]
    offset: int
    limit: int


def list_tags(
    session: Session, user: CurrentUser, input: ListTagsInput
) -> ListTagsResults:
    statement = (
        select(Tag)
        .where(user.organization_id == Tag.organization_id)
        .offset(input.offset)
        .limit(input.limit)
    )

    if input.name:
        statement = statement.where(Tag.name.contains(input.name))

    results = session.exec(statement).all()
    return ListTagsResults(results=results, offset=input.offset, limit=input.limit)


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
    raise Exception("Tag not found")


def list_tag_contents(
    session: Session,
    user: CurrentUser,
    tag_id: str,
    limit: int,
    offset: int,
    content_type_ids: list[str],
) -> ListTagContentsResults:
    tag = session.exec(
        select(Tag)
        .join(TagContent, isouter=True)
        .join(
            DerivedContent,
            isouter=True,
            onclause=(
                and_(
                    TagContent.content_id == DerivedContent.id,
                    DerivedContent.content_type_id.in_(content_type_ids),
                )
            ),
        )
        .where(Tag.id == tag_id and Tag.organization_id == user.organization_id)
        .offset(offset)
        .limit(limit)
    ).first()

    if not tag:
        raise Exception("Not found")

    return ListTagContentsResults(
        tag=tag,
        content_type_ids=content_type_ids,
        results=[
            tag
            for tag in tag.derived_contents
            if tag.content_type_id in content_type_ids
        ],
        offset=offset,
        limit=limit,
    )
