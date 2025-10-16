from uuid import UUID

from database.models import Node
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action
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
    query = select(Node).where(Node.id == node_id).options(selectinload(Node.version))
    node = session.exec(query).one()
    primary_asset_id = node.version.primary_asset_id
    enforce_asset_action(
        db=session, user=user, asset_id=primary_asset_id, action_key="pdf.download"
    )
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
    # TODO: session is unneeded here, don't need content service, just the logic to convert MD to RST
    rst_content = content_service.convert_markdown_to_rst(request.content)
    return StreamingResponse(
        rst_content,
        media_type="text/x-rst",
        headers={"Content-Disposition": "attachment; filename=exported_content.rst"},
    )
