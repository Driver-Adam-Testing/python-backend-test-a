from database.models_v1 import Tag
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.core.logger import logging
from app.utils.tags import (
    ListTagContentsResults,
    ListTagsInput,
    ListTagsResults,
    NewTagInput,
    create_tag,
    edit_tag,
    list_tag_contents,
    list_tags,
)

router = APIRouter()


# Create a new tag
@router.post("/", status_code=201)
def new_tag(session: CurrentSession, user: CurrentUser, newTag: NewTagInput) -> Tag:
    logging.info("Creating new tag")
    try:
        return create_tag(session=session, user=user, input=newTag)
    except IntegrityError:
        logging.error("Tag name already exists")
        raise HTTPException(status_code=400, detail="Tag name already exists.")


# Read all tags
@router.get("/")
def read_tags(
    session: CurrentSession,
    user: CurrentUser,
    limit: int | None = 20,
    offset: int | None = 0,
    name: str | None = None,
) -> ListTagsResults:
    return list_tags(
        session=session,
        user=user,
        input=ListTagsInput(limit=limit, offset=offset, name=name),
    )


# Update a tag - all users in an organization can edit all tags in the organization
@router.put("/{tag_id}")
def update_tag(
    session: CurrentSession, user: CurrentUser, tag_id: str, updatedTag: NewTagInput
) -> Tag:
    try:
        return edit_tag(session=session, user=user, tag_id=tag_id, input=updatedTag)
    except Exception as ex:
        logging.error("Tag not found for update", exc_info=ex)
        raise HTTPException(status_code=404, detail="Tag not found")


@router.get("/{tag_id}/content")
def read_tag_contents(
    session: CurrentSession,
    user: CurrentUser,
    tag_id: str,
    content_type_id: list[str] = Query([], min_length=1),
    limit: int | None = 20,
    offset: int | None = 0,
) -> ListTagContentsResults:
    try:
        return list_tag_contents(
            session=session,
            user=user,
            tag_id=tag_id,
            content_type_ids=content_type_id,
            limit=limit,
            offset=offset,
        )
    except Exception as ex:
        logging.exception("Tag content not found", exc_info=ex)
        raise HTTPException(status_code=404, detail="Tag content not found")
