from database.models_v1 import Tag
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.core.logger import logging
from app.utils.tags import (
    ListTagsInput,
    ListTagsResults,
    NewTagInput,
    create_tag,
    edit_tag,
    list_tags,
)

router = APIRouter()


# Create a new tag
@router.post("/", status_code=201)
def new_tag(session: CurrentSession, user: CurrentUser, newTag: NewTagInput) -> Tag:
    try:
        return create_tag(session=session, user=user, input=newTag)
    except IntegrityError:
        logging.error("Tag name already exists")
        raise HTTPException(status_code=400, detail="Tag name already exists.")
    except Exception as ex:
        logging.error("Internal Server Error")
        logging.error(ex)
        raise HTTPException(status_code=500, detail="Internal server error")


# Read all tags
@router.get("/")
def read_tags(
    session: CurrentSession,
    user: CurrentUser,
    limit: int | None = 20,
    offset: int | None = 0,
    name: str | None = None,
    user_id: str | None = None,
) -> ListTagsResults:
    return list_tags(
        session=session,
        user=user,
        input=ListTagsInput(limit=limit, offset=offset, name=name, user_id=user_id),
    )


# Update a tag - all users in an organization can edit all tags in the organization
@router.put("/{tag_id}")
def update_tag(
    session: CurrentSession, user: CurrentUser, tag_id: str, updatedTag: NewTagInput
) -> Tag:
    try:
        return edit_tag(session=session, user=user, tag_id=tag_id, input=updatedTag)
    except Exception:
        raise HTTPException(status_code=404, detail="Tag not found")


# Delete a tag
# @router.delete("/tags/{tag_id}", status_code=204)
