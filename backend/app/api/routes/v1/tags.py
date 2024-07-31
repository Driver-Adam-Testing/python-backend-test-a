import logging
from typing import Annotated

from database.models_v1 import Tag
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.utils.content import (
    ListContentInput,
    TagAssociationResponse,
    associate_tag,
    disassociate_tag,
)
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


logger = logging.getLogger(__name__)


# Create a new tag
@router.post("/", status_code=201)
def new_tag(session: CurrentSession, user: CurrentUser, new_tag: NewTagInput) -> Tag:
    logging.info("Creating new tag")
    try:
        return create_tag(session=session, user=user, input=new_tag)
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
    content_type_id: Annotated[list[str] | None, Query()] = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    text: str | None = None,
    workspace_id: str | None = None,
    limit: int | None = 20,
    offset: int | None = 0,
) -> ListTagContentsResults:
    try:
        return list_tag_contents(
            session=session,
            user=user,
            tag_id=tag_id,
            input=ListContentInput(
                limit=limit,
                offset=offset,
                text=text,
                content_type_id=content_type_id,
                sort_by=sort_by,
                sort_direction=sort_direction,
                status=status,
                workspace_id=workspace_id,
            ),
        )
    except Exception as ex:
        logging.exception("Tag content not found", exc_info=ex)
        raise HTTPException(status_code=404, detail="Tag content not found")


@router.post(
    "/{tag_id}/content/{content_id}",
    summary="Associate a tag with this content",
)
def associate_tag_with_content(
    session: CurrentSession,
    user: CurrentUser,
    content_id: str,
    tag_id: str,
) -> TagAssociationResponse:
    try:
        return associate_tag(session, user, content_id, tag_id)
    except IntegrityError:
        logging.error("Association already exists.")
        raise HTTPException(
            status_code=400,
            detail="Association already exists, please check your parameters.",
        )
    except Exception as ex:
        logging.exception("Unable to find tag or content.", exc_info=ex)
        raise HTTPException(
            status_code=404,
            detail="Unable to find tag or content, please check your parameters.",
        )


@router.delete(
    "/{tag_id}/content/{content_id}",
    summary="Disassociate a tag with this content",
)
def disassociate_tag_with_content(
    session: CurrentSession,
    user: CurrentUser,
    content_id: str,
    tag_id: str,
) -> TagAssociationResponse:
    try:
        return disassociate_tag(session, user, content_id, tag_id)
    except Exception as ex:
        logging.exception("Association not found", exc_info=ex)
        raise HTTPException(status_code=404, detail="Association not found")
