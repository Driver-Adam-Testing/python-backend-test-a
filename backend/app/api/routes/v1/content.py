import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.utils.content import (
    ListContentInput,
    ListContentResults,
    ListContentTypesInput,
    ListContentTypesResults,
    TagAssociationResponse,
    associate_tag,
    disassociate_tag,
    list_content,
    list_content_types,
)

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get(
    "/",
    summary="List content matching the provided filter criteria",
)
def list(
    session: CurrentSession,
    user: CurrentUser,
    limit: int | None = 20,
    offset: int | None = 0,
    content_type_id: Annotated[list[str] | None, Query()] = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    tag: Annotated[list[str] | None, Query()] = None,
    text: str | None = None,
    workspace_id: str | None = None,
) -> ListContentResults:
    return list_content(
        session,
        user,
        ListContentInput(
            limit=limit,
            offset=offset,
            text=text,
            content_type_id=content_type_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
            status=status,
            tags=tag,
            workspace_id=workspace_id,
        ),
    )


@router.get(
    "/types",
    summary="List content types",
)
def list_types(
    session: CurrentSession,
    user: CurrentUser,
    limit: int | None = 20,
    offset: int | None = 0,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
) -> ListContentTypesResults:
    return list_content_types(
        session,
        ListContentTypesInput(
            limit=limit, offset=offset, sort_by=sort_by, sort_direction=sort_direction
        ),
    )


@router.post(
    "/{content_id}/tags/{tag_id}",
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
    "/{content_id}/tags/{tag_id}",
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
