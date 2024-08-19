import logging
from typing import Annotated

from database.models_v1 import Tag
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.schemas.content_schema import ListContentInput, TagAssociationResponse
from app.schemas.tag_schema import (
    EditTagInput,
    ListTagContentsResults,
    ListTagsInput,
    ListTagsResults,
    NewTagInput,
    TagType,
)
from app.services.tag_service import TagService, get_tag_service

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/", status_code=201)
def new_tag(
    user: CurrentUser,
    new_tag: NewTagInput,
    tag_service: TagService = Depends(get_tag_service),
) -> Tag:
    logging.info("Creating new tag")
    logging.debug(new_tag)
    try:
        return tag_service.create_tag(user=user, lt_input=new_tag)
    except IntegrityError:
        logging.error("Tag name already exists")
        raise HTTPException(status_code=400, detail="Tag name already exists.")


@router.get("/")
def read_tags(
    user: CurrentUser,
    limit: int | None = 20,
    offset: int | None = 0,
    name: str | None = None,
    type: TagType | None = None,
    tag_service: TagService = Depends(get_tag_service),
) -> ListTagsResults:
    return tag_service.list_tags(
        user=user,
        lt_input=ListTagsInput(limit=limit, offset=offset, name=name, type=type),
    )


@router.put("/{tag_id}")
def update_tag(
    user: CurrentUser,
    tag_id: str,
    updated_tag: EditTagInput,
    tag_service: TagService = Depends(get_tag_service),
) -> Tag:
    """Update a tag. All users in an organization can edit all tags in the organization currently."""
    return tag_service.edit_tag(user=user, tag_id=tag_id, lt_input=updated_tag)


@router.get("/{tag_id}/content")
def read_tag_contents(
    user: CurrentUser,
    tag_id: str,
    content_type_id: Annotated[list[str] | None, Query()] = None,
    content_type_name: Annotated[list[str] | None, Query()] = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    text: str | None = None,
    limit: int | None = 20,
    offset: int | None = 0,
    tag_service: TagService = Depends(get_tag_service),
) -> ListTagContentsResults:
    return tag_service.list_tag_contents(
        user=user,
        tag_id=tag_id,
        lt_input=ListContentInput(
            limit=limit,
            offset=offset,
            text=text,
            content_type_id=content_type_id,
            content_type_name=content_type_name,
            sort_by=sort_by,
            sort_direction=sort_direction,
            status=status,
        ),
    )


@router.post(
    "/{tag_id}/content/{content_id}",
    summary="Associate a tag with this content",
)
def associate_tag_with_content(
    session: CurrentSession,
    user: CurrentUser,
    content_id: str,
    tag_id: str,
    tag_service: TagService = Depends(get_tag_service),
) -> TagAssociationResponse:
    try:
        return tag_service.associate_tag(session, user, content_id, tag_id)
    except IntegrityError:
        logging.error("Association already exists.")
        raise HTTPException(
            status_code=400,
            detail="Association already exists, please check your parameters.",
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
    tag_service: TagService = Depends(get_tag_service),
) -> TagAssociationResponse:
    return tag_service.disassociate_tag(session, user, content_id, tag_id)
