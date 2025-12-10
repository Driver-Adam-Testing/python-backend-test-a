import logging
from typing import Annotated
from uuid import UUID

from database.models import Tag
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_org_membership
from app.schemas.content_schema import ListContentInput
from app.schemas.tag_schema import (
    EditTagInput,
    ListTagContentsResults,
    ListTagsInput,
    ListTagsResults,
    NewTagInput,
    TagType,
)
from app.services.tag_service import TagService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/", status_code=201)
def new_tag(
    session: CurrentSession,
    user: UserToken,
    new_tag: NewTagInput,
) -> Tag:
    enforce_org_membership(session, user)
    logger.info("Creating new tag")
    tag_service = TagService(session)
    return tag_service.create_tag(user=user, lt_input=new_tag)


@router.get("/")
def read_tags(
    session: CurrentSession,
    user: UserToken,
    limit: int | None = 20,
    offset: int | None = 0,
    name: str | None = None,
    type: TagType | None = None,
) -> ListTagsResults:
    enforce_org_membership(session, user)
    tag_service = TagService(session)
    return tag_service.list_tags(
        user=user,
        lt_input=ListTagsInput(limit=limit, offset=offset, name=name, type=type),
    )


@router.put("/{tag_id}")
def update_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: str,
    updated_tag: EditTagInput,
) -> Tag:
    enforce_org_membership(session, user)
    """Update a tag. All users in an organization can edit all tags in the organization currently."""
    tag_service = TagService(session)
    return tag_service.edit_tag(user=user, tag_id=tag_id, lt_input=updated_tag)


@router.get("/{tag_id}/content")
def read_tag_contents(
    session: CurrentSession,
    user: UserToken,
    tag_id: str,
    content_type_name: Annotated[list[str] | None, Query()] = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    text: str | None = None,
    limit: int | None = 20,
    offset: int | None = 0,
    latest_version_only: bool = False,
) -> ListTagContentsResults:
    enforce_org_membership(session, user)
    tag_service = TagService(session)
    return tag_service.list_tag_contents(
        user=user,
        tag_id=tag_id,
        lt_input=ListContentInput(
            latest_version_only=latest_version_only,
            limit=limit,
            offset=offset,
            text=text,
            content_type_name=content_type_name,
            sort_by=sort_by,
            sort_direction=sort_direction,
            status=status,
        ),
    )


@router.delete("/{tag_id}", status_code=204)
def delete_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: UUID,
) -> None:
    """Delete a tag by its ID."""
    enforce_org_membership(session, user)
    tag_service = TagService(session)
    try:
        tag_service.delete_tag(user=user, tag_id=tag_id)
    except IntegrityError as e:
        logger.error(f"Integrity error deleting tag {tag_id}: {e}")
        raise HTTPException(400, "Cannot delete tag due to existing references.")
