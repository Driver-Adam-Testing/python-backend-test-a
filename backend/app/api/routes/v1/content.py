from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.content_schema import (
    BatchContentSourceAssociationRequest,
    BatchContentSourceAssociationResponse,
    BatchDeleteDocumentSourceResponse,
    ContentSourceAssociationRequest,
    ContentSourceAssociationResponse,
    ContentSourceResponse,
    CreateContentRequest,
    CreateContentResponse,
    DeleteContentSourcesRequest,
    DeleteDocumentSourceResponse,
    ListContentInput,
    ListContentResults,
    ListContentTypesInput,
    ListContentTypesResults,
    TagAssociationResponse,
)
from app.schemas.tag_schema import CollectionSourceInput
from app.services.content_service import ContentService

router = APIRouter()


@router.get(
    "/",
    summary="List content matching the provided filter criteria",
)
def list_content(
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
    content_service = ContentService(session)
    results = content_service.get_list_content(
        user.organization_id,
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
    return results


@router.get(
    "/types",
    summary="List content types",
)
def list_content_types(
    session: CurrentSession,
    user: CurrentUser,
    limit: int | None = 20,
    offset: int | None = 0,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
) -> ListContentTypesResults:
    content_service = ContentService(session)
    return content_service.get_list_content_types(
        ListContentTypesInput(
            limit=limit, offset=offset, sort_by=sort_by, sort_direction=sort_direction
        )
    )


@router.get(
    "/{content_id}",
    summary="Get content by ID",
)
def get_content_by_id(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
):
    content_service = ContentService(session)
    return content_service.get_content_by_id(content_id, user.organization_id)


@router.get(
    "/{content_id}/codebase-root",
    summary="Get codebase content record for this.",
)
def get_codebase_root(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
):
    """
    Get the root codebase content record for a given content ID. this is need by the frontend to appropriately
    add document sources.
    """
    content_service = ContentService(session)
    return content_service.get_content_root_by_id(content_id, user.organization_id)


@router.get(
    "/{content_id}/document-sources",
    summary="Get sources associated with a document",
)
def get_document_sources(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
) -> ContentSourceResponse:
    content_service = ContentService(session)
    return content_service.get_content_sources(content_id, user.organization_id)


@router.post(
    "/{content_id}/tags/{tag_id}",
    summary="Associate a tag with this content",
)
def associate_tag(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
    tag_id: UUID,
    input: CollectionSourceInput,
) -> TagAssociationResponse:
    content_service = ContentService(session)
    return content_service.associate_tag(
        user.organization_id, content_id, tag_id, include_tag=input.include
    )


@router.post(
    "/{content_id}/document-sources/{source_content_id}",
    summary="Associate one source content item with this content.",
)
def associate_sources(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
    source_content_id: UUID,
    body: ContentSourceAssociationRequest,
) -> ContentSourceAssociationResponse:
    content_service = ContentService(session)

    return content_service.associate_document_source(
        user.organization_id, content_id, source_content_id, include=body.include
    )


@router.post(
    "/{content_id}/document-sources/batch/",
    summary="Associate multiple sources with this content.",
)
def batch_associate_sources(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
    content_source_associations: BatchContentSourceAssociationRequest,
) -> BatchContentSourceAssociationResponse:
    content_service = ContentService(session)
    return content_service.associate_sources_with_content(
        user.organization_id, content_id, content_source_associations.sources
    )


@router.post(
    "/",
    summary="Create a new content item.",
)
def create_content(
    session: CurrentSession,
    user: CurrentUser,
    request: CreateContentRequest,
):
    content_service = ContentService(session)
    content = content_service.create_blank_document(
        user.organization_id, request.workspace_id, request.codebase_id
    )
    return content


@router.post("/document", summary="Create a document", deprecated=True)
def create_document(
    session: CurrentSession,
    user: CurrentUser,
    request: CreateContentRequest,
) -> CreateContentResponse:
    content_service = ContentService(session)
    result = content_service.create_blank_document(
        user.organization_id, request.workspace_id, request.codebase_id
    )
    return CreateContentResponse(results=[result])


@router.delete(
    "/{content_id}/tags/{tag_id}",
    summary="Disassociate a tag with this content",
)
def disassociate_tag(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
    tag_id: UUID,
) -> TagAssociationResponse:
    content_service = ContentService(session)
    return content_service.disassociate_tag(user.organization_id, content_id, tag_id)


@router.delete(
    "/{content_id}/document-sources/{source_content_id}",
    summary="Disassociate a source content item from this content",
)
def disassociate_source(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
    source_content_id: UUID,
) -> DeleteDocumentSourceResponse:
    content_service = ContentService(session)
    return content_service.disassociate_document_source(
        user.organization_id, content_id, source_content_id
    )


@router.delete(
    "/{content_id}/document-sources/batch/",
    summary="Disassociate multiple sources from this content",
)
def batch_disassociate_sources(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
    source_content_associations: DeleteContentSourcesRequest,
) -> BatchDeleteDocumentSourceResponse:
    content_service = ContentService(session)
    results = []
    for source_id in source_content_associations.source_ids:
        try:
            result = content_service.disassociate_document_source(
                user.organization_id, content_id, source_id
            )
            results.append(result)
        except Exception as e:
            logger.error(
                f"Failed to disassociate source {source_id} from content {content_id}: {e}"
            )
            results.append(
                DeleteDocumentSourceResponse(
                    document_id=content_id,
                    source_id=source_id,
                    message="Failed to disassociate source",
                )
            )
    return BatchDeleteDocumentSourceResponse(results=results)


# @router.post(
#     "/from-template",
#     summary="Create a content record from a template content record",
#     deprecated=True
# )
# def create_content_from_template(
#         session: CurrentSession,
#         user: CurrentUser,
#         request: CreateTemplateRequest,
# ) -> CreateContentResponse:
#     content_service = ContentService(session)
#     result = content_service.create_document_from_template(
#         user.organization_id, request.content_id
#     )
#     return CreateContentResponse(results=[result])


# @router.post(
#     "/template",
#     summary="Create a template content record",
#     deprecated=True
# )
# def create_template(
#         session: CurrentSession,
#         user: CurrentUser,
#         request: CreateTemplateRequest,
# ) -> CreateContentResponse:
#     content_service = ContentService(session)
#     result = content_service.create_template(
#         user.organization_id, request.workspace_id, request.codebase_id
#     )
#     return CreateContentResponse(results=[result])
