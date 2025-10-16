from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession
from app.schemas.content_schema import (
    DownloadContentResponse,
    ExportSingleRequest,
)
from app.services.content_service import ContentService

router = APIRouter()


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
