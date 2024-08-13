import logging
from typing import Annotated

from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlmodel import Session

from app.api.auth import CurrentUser
from app.api.content.content import (
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

from app.schemas.content_schema import CreateContentRequest, CreateContentResponse, CreateTemplateRequest

from app.services.content_service import (ContentService, get_content_service)

from database.models_v1 import DerivedContent

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
        content_service: ContentService = Depends(get_content_service),
) -> ListContentResults:
    results = content_service.get_list_content(user.organization_id, ListContentInput(
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
    ))
    return results


@router.get(
    "/types",
    summary="List content types",
)
def list_types(
        limit: int | None = 20,
        offset: int | None = 0,
        sort_by: str | None = None,
        sort_direction: str | None = "ASC",
        content_service: ContentService = Depends(get_content_service),
) -> ListContentTypesResults:
    return content_service.get_list_content_types(ListContentTypesInput(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_direction=sort_direction
    ))


@router.post(
    "/{content_id}/tags/{tag_id}",
    summary="Associate a tag with this content",
)
def associate_tag_with_content(
        user: CurrentUser,
        content_id: str,
        tag_id: str,
        content_service: ContentService = Depends(get_content_service),
) -> TagAssociationResponse:
    return content_service.associate_tag(user.organization_id, content_id, tag_id)



@router.delete(
    "/{content_id}/tags/{tag_id}",
    summary="Disassociate a tag with this content",
)
def disassociate_tag_with_content(
        user: CurrentUser,
        content_id: str,
        tag_id: str,
        content_service: ContentService = Depends(get_content_service),
) -> TagAssociationResponse:
    return content_service.disassociate_tag(user.organization_id, content_id, tag_id)


@router.post(
    "/document",
    summary="Create a document",
)
def create_document(
        user: CurrentUser,
        request: CreateContentRequest,
        content_service: ContentService = Depends(get_content_service),
) -> CreateContentResponse:
    return CreateContentResponse(
        results=[
            content_service.create_blank_document(user.organization_id, request.workspace_id, request.codebase_id)
        ]
    )


@router.post(
    "/from-template",
    summary="Create a content record from a template content record",
)
def create_from_template(
        session: CurrentSession,
        user: CurrentUser,
        request: CreateTemplateRequest,
        content_service: ContentService = Depends(get_content_service)
) -> CreateContentResponse:
    return CreateContentResponse(
        results=[
            content_service.create_content_from_template(session, user, request.content_id)
        ]
    )


@router.post(
    "/template",
    summary="Create a template content record",
)
def create_template_content_record(
        session: CurrentSession,
        user: CurrentUser,
        request: CreateTemplateRequest,
        content_service: ContentService = Depends(get_content_service),
) -> CreateContentResponse:
    return CreateContentResponse(
        results=[
            content_service.create_template(session, user, request.content_id)
        ]
    )
