from database.models_v1 import Tag
from pydantic import BaseModel
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

    if input.user_id:
        statement = statement.where(Tag.created_by == input.user_id)

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
    tag = session.get(Tag, tag_id)
    if tag and tag.organization_id == user.organization_id:
        tag.name = input.name.strip()
        tag.hex_color = input.hexColor.strip()
        tag.updated_by = user.user_id
        session.commit()
        session.refresh(tag)
        return tag
    raise Exception("Tag not found")


# TODO: check for existing relationships
# def delete_tag(session: Session, user: CurrentUser, tag_id: int) -> None:
#     tag = session.get(Tag, tag_id)
#     if tag and tag:
#         session.delete(tag)
#         session.commit()
