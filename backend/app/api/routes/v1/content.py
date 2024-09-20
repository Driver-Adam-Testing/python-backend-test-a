from typing import Annotated
from uuid import UUID

from database.models_v1 import DerivedContent
from fastapi import APIRouter, Query

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.content_schema import (
    BatchContentSourceAssociationRequest,
    BatchContentSourceAssociationResponse,
    BatchDeleteDocumentSourceResponse,
    ContentSourceResponse,
    CreateContentRequest,
    DeleteContentSourcesRequest,
    DeleteDocumentSourceResponse,
    DownloadContentResponse,
    ListContentInput,
    ListContentResults,
    ListContentTypesInput,
    ListContentTypesResults,
)
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
    """
    List content matching the provided filter criteria.

    Parameters:
    - session: Current session object
    - user: Current user object
    - limit: Maximum number of items to return
    - offset: Number of items to skip
    - content_type_id: List of content type IDs to filter by
    - content_type_name: List of content type names to filter by
    - sort_by: Field to sort by
    - sort_direction: Direction to sort (ASC or DESC)
    - status: Status to filter by
    - tag: List of tags to filter by
    - tag_id: List of tag IDs to filter by
    - text: Text to search for in content

    Returns:
    - ListContentResults: Results of the content list query
    """
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
def get_list_content_types(
    session: CurrentSession,
    limit: int | None = 20,
    offset: int | None = 0,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
) -> ListContentTypesResults:
    """
    List content types.

    Parameters:
    - session: Current session object
    - limit: Maximum number of items to return
    - offset: Number of items to skip
    - sort_by: Field to sort by
    - sort_direction: Direction to sort (ASC or DESC)

    Returns:
    - ListContentTypesResults: Results of the content types list query
    """
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
) -> DerivedContent:
    """
    Get content by ID.

    Parameters:
    - session: Current session object
    - user: Current user object
    - content_id: UUID of the content

    Returns:
    - DerivedContent: Content details
    """
    content_service = ContentService(session)
    return content_service.get_content_by_id(content_id, user.organization_id)


@router.get(
    "/{content_id}/download",
    summary="Get download URL from S3 by ID",
)
def get_download_content_by_id(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
) -> DownloadContentResponse:
    """
    Get download URL from S3 by ID

    Parameters:
    - session: Current session object
    - user: Current user object
    - content_id: UUID of the content

    Returns:
    - DerivedContent: Content details
    """
    content_service = ContentService(session)
    return content_service.get_content_download_url(content_id, user.organization_id)


@router.get(
    "/{content_id}/codebase-root",
    summary="Get root codebase content record for this.",
)
def get_content_root_by_id(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
) -> DerivedContent:
    """
    Get the root codebase content record for a given content ID. This is needed by the frontend to appropriately
    add document sources.

    Parameters:
    - session: Current session object
    - user: Current user object
    - content_id: UUID of the content

    Returns:
    - DerivedContent: Root codebase content details
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
    """
    Get sources associated with a document.

    Parameters:
    - session: Current session object
    - user: Current user object
    - content_id: UUID of the content

    Returns:
    - ContentSourceResponse: Document sources details
    """
    content_service = ContentService(session)
    return content_service.get_content_sources(content_id, user.organization_id)


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
    """
    Associate multiple sources with this content.

    Parameters:
    - session: Current session object
    - user: Current user object
    - content_id: UUID of the content
    - content_source_associations: BatchContentSourceAssociationRequest object containing the list of sources

    Returns:
    - BatchContentSourceAssociationResponse: Batch source association details
    """
    content_service = ContentService(session)
    return content_service.associate_sources_with_content(
        user.organization_id, content_id, content_source_associations.sources
    )


@router.post(
    "/",
    summary="Create a blank application note.",
)
def create_blank_document(
    session: CurrentSession,
    user: CurrentUser,
    request: CreateContentRequest,
) -> DerivedContent:
    """
    Create a blank application note.

    Parameters:
    - session: Current session object
    - user: Current user object
    - request: CreateContentRequest object containing the optional workspace_id and codebase_id and content_type

    Returns:
    - DerivedContent: Created content details
    """
    content_service = ContentService(session)
    return content_service.create_content(user.organization_id, request)


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
    """
    Disassociate multiple sources from this content.

    Parameters:
    - session: Current session object
    - user: Current user object
    - content_id: UUID of the content
    - source_content_associations: DeleteContentSourcesRequest object containing the list of source IDs

    Returns:
    - BatchDeleteDocumentSourceResponse: Batch source disassociation details
    """
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


@router.put(
    "/{content_id}/",
    summary="Update content by ID",
)
def update_content(
    session: CurrentSession,
    user: CurrentUser,
    content_id: UUID,
    update_data: dict,  # TODO add validation
) -> DerivedContent:
    content_service = ContentService(session)
    return content_service.edit_content(user.organization_id, content_id, update_data)
