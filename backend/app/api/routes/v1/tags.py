import logging
from typing import Annotated
from uuid import UUID

from database.models_v1 import Tag
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.api.auth import (
    ContentEditorPermission,
    ContentReadonlyPermission,
    UserToken,
)
from app.api.session import CurrentSession
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


@router.post(
    "/",
    status_code=201,
    dependencies=[ContentEditorPermission],
)
def new_tag(
    session: CurrentSession,
    user: UserToken,
    new_tag: NewTagInput,
) -> Tag:
    logging.info("Creating new tag")
    tag_service = TagService(session)
    return tag_service.create_tag(user=user, lt_input=new_tag)


@router.get("/", dependencies=[ContentReadonlyPermission])
def read_tags(
    session: CurrentSession,
    user: UserToken,
    limit: int | None = 20,
    offset: int | None = 0,
    name: str | None = None,
    type: TagType | None = None,
) -> ListTagsResults:
    tag_service = TagService(session)
    return tag_service.list_tags(
        user=user,
        lt_input=ListTagsInput(limit=limit, offset=offset, name=name, type=type),
    )


@router.put(
    "/{tag_id}",
    dependencies=[ContentEditorPermission],
)
def update_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: str,
    updated_tag: EditTagInput,
) -> Tag:
    """Update a tag. All users in an organization can edit all tags in the organization currently."""
    tag_service = TagService(session)
    return tag_service.edit_tag(user=user, tag_id=tag_id, lt_input=updated_tag)


@router.get("/{tag_id}/content", dependencies=[ContentReadonlyPermission])
def read_tag_contents(
    session: CurrentSession,
    user: UserToken,
    tag_id: str,
    content_type_id: Annotated[list[str] | None, Query()] = None,
    content_type_name: Annotated[list[str] | None, Query()] = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    text: str | None = None,
    limit: int | None = 20,
    offset: int | None = 0,
    latest_version_only: bool = False,
) -> ListTagContentsResults:
    tag_service = TagService(session)
    return tag_service.list_tag_contents(
        user=user,
        tag_id=tag_id,
        lt_input=ListContentInput(
            latest_version_only=latest_version_only,
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


@router.delete("/{tag_id}", status_code=204, dependencies=[ContentEditorPermission])
def delete_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: UUID,
) -> None:
    """Delete a tag by its ID."""
    tag_service = TagService(session)
    try:
        tag_service.delete_tag(user=user, tag_id=tag_id)
        return  # No content should be returned for 204 status code
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))
