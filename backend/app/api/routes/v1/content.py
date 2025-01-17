from typing import Annotated
from uuid import UUID

from database.models_v1 import DerivedContent
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.content_schema import (
    BatchContentSourceAssociationRequest,
    BatchContentSourceAssociationResponse,
    BatchDeleteDocumentSourceResponse,
    ContentSourceResponse,
    ContentTagsResponse,
    DeleteContentSourcesRequest,
    DeleteDocumentSourceResponse,
    DownloadContentResponse,
    ExportSingleRequest,
    ListContentInput,
    ListContentResults,
)
from app.services.content_service import ContentService

router = APIRouter()


@router.get(
    "/",
    summary="List content matching the provided filter criteria",
    dependencies=[ContentReadonlyPermission],
)
def list_content(
    session: CurrentSession,
    user: UserToken,
    latest_version_only: bool = False,
    limit: int | None = 20,
    offset: int | None = 0,
    content_type_id: Annotated[list[str] | None, Query()] = None,
    content_type_name: Annotated[list[str] | None, Query()] = None,
    source_content_id: Annotated[list[str] | None, Query()] = None,
    order: int | None = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    tag: Annotated[list[str] | None, Query()] = None,
    tag_id: Annotated[list[str] | None, Query()] = None,
    text: str | None = None,
    version_id: Annotated[list[str] | None, Query()] = None,
) -> ListContentResults:
    content_service = ContentService(session)
    results = content_service.get_list_content(
        user.organization_id,
        ListContentInput(
            latest_version_only=latest_version_only,
            limit=limit,
            offset=offset,
            text=text,
            content_type_id=content_type_id,
            source_content_id=source_content_id,
            order=order,
            content_type_name=content_type_name,
            sort_by=sort_by,
            sort_direction=sort_direction,
            status=status,
            tags=tag,
            tag_ids=tag_id,
            version_id=version_id,
        ),
    )
    return results


@router.get(
    "/{content_id}",
    summary="Get content by ID",
    dependencies=[ContentReadonlyPermission],
)
def get_content_by_id(
    session: CurrentSession,
    user: UserToken,
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
    "/{node_id}/download",
    summary="Get download URL from S3 by ID",
    dependencies=[ContentReadonlyPermission],
)
def get_download_content_by_id(
    session: CurrentSession,
    user: UserToken,
    node_id: UUID,
) -> DownloadContentResponse:
    """
    Get download URL from S3 by ID

    Parameters:
    - session: Current session object
    - user: Current user object
    - node_id: UUID of the node

    Returns:
    - DerivedContent: Content details
    """
    content_service = ContentService(session)
    return content_service.get_content_download_url(node_id, user.organization_id)


@router.get(
    "/{content_id}/codebase-root",
    summary="Get root codebase content record for this.",
    dependencies=[ContentReadonlyPermission],
)
def get_content_root_by_id(
    session: CurrentSession,
    user: UserToken,
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
    dependencies=[ContentReadonlyPermission],
)
def get_document_sources(
    session: CurrentSession,
    user: UserToken,
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
    dependencies=[ContentEditorPermission],
)
def batch_associate_sources(
    session: CurrentSession,
    user: UserToken,
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


@router.delete(
    "/{content_id}/document-sources/batch/",
    summary="Disassociate multiple sources from this content",
    dependencies=[ContentEditorPermission],
)
def batch_disassociate_sources(
    session: CurrentSession,
    user: UserToken,
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
    dependencies=[ContentEditorPermission],
)
def update_content(
    session: CurrentSession,
    user: UserToken,
    content_id: UUID,
    update_data: dict,  # TODO add validation
) -> DerivedContent:
    content_service = ContentService(session)
    return content_service.edit_content(user.organization_id, content_id, update_data)


@router.delete(
    "/{content_id}/", status_code=204, dependencies=[ContentEditorPermission]
)
def delete_content(
    session: CurrentSession,
    user: UserToken,
    content_id: UUID,
) -> None:
    content_service = ContentService(session)
    content_service.delete_content(user.organization_id, content_id)
    return


@router.get(
    "/{content_id}/tags",
    summary="Get tags associated with a content",
    dependencies=[ContentReadonlyPermission],
)
def get_content_tags(
    session: CurrentSession,
    user: UserToken,
    content_id: UUID,
) -> ContentTagsResponse:
    """
    Get tags associated with a content.

    Parameters:
    - session: Current session object
    - user: Current user object
    - content_id: UUID of the content

    Returns:
    - ContentTagsResponse: Response containing the list of tags associated with the content
    """
    content_service = ContentService(session)
    return content_service.get_content_tags(content_id, user.organization_id)


@router.post(
    "/export-rst",
    summary="Export Markdown content to RST and return the file",
    dependencies=[ContentEditorPermission],
)
def export_markdown_content_to_rst(
    session: CurrentSession,
    request: ExportSingleRequest,
) -> StreamingResponse:
    content_service = ContentService(session)
    rst_content = content_service.convert_markdown_to_rst(request.content)
    return StreamingResponse(
        rst_content,
        media_type="text/x-rst",
        headers={"Content-Disposition": "attachment; filename=exported_content.rst"},
    )
