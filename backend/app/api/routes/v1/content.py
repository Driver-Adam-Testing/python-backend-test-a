import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.auth import CurrentUser
from app.api.content.content import (
    CreateContentRequest,
    CreateContentResponse,
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
from app.api.session import CurrentSession
from app.schemas.content_schema import (
    CreateTemplateRequest,
)
from app.services.content_service import ContentService, get_content_service

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
    content_type_name: Annotated[list[str] | None, Query()] = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    tag: Annotated[list[str] | None, Query()] = None,
    tag_id: Annotated[list[str] | None, Query()] = None,
    text: str | None = None,
) -> ListContentResults:
    return list_content(
        session,
        user,
        ListContentInput(
            limit=limit,
            offset=offset,
            text=text,
            content_type_id=content_type_id,
            content_type_name=content_type_name,
            sort_by=sort_by,
            sort_direction=sort_direction,
            status=status,
            tags=tag,
            tag_ids=tag_id,
        ),
    )


@router.get(
    "/types",
    summary="List content types",
)
def list_types(
    session: CurrentSession,
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
    return associate_tag(session, user, content_id, tag_id)


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
    return disassociate_tag(session, user, content_id, tag_id)


@router.post(
    "/create/document",
    summary="Create a document",
)
def create_document(
    user: CurrentUser,
    request: CreateContentRequest,
    content_service: ContentService = Depends(get_content_service),
) -> CreateContentResponse:
    return content_service.create_blank_document(
        user.organization_id, request.workspace_id, request.codebase_id
    )


@router.post(
    "/create/from-template",
    summary="Create a content record from a template content record",
)
def create_from_template(
    session: CurrentSession,
    user: CurrentUser,
    request: CreateTemplateRequest,
    content_service: ContentService = Depends(get_content_service),
) -> CreateContentResponse:
    return content_service.create_content_from_template(
        session, user, request.content_id
    )


@router.post(
    "/create/template",
    summary="Create a template content record",
)
def create_template_content_record(
    session: CurrentSession,
    user: CurrentUser,
    request: CreateTemplateRequest,
    content_service: ContentService = Depends(get_content_service),
) -> CreateContentResponse:
    return content_service.create_template(session, user, request.content_id)
