from uuid import UUID

from database.models import Version, VersionNode
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action
from app.schemas.content_schema import (
    DownloadContentResponse,
    ExportSingleRequest,
)
from app.services.content_service import ContentService

router = APIRouter()

# FURNISSJ: change node_id to version_node_id
@router.get(
    "/{node_id}/download",
    summary="Get download URL from S3 by ID",
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
    query = (
        select(VersionNode)
        .where(VersionNode.id == node_id)
        .options(selectinload(VersionNode.version))
        .options(selectinload(Version.primary_asset))
    )
    version_node = session.exec(query).one()
    primary_asset_id = version_node.version.primary_asset.id
    enforce_asset_action(
        db=session, user=user, asset_id=primary_asset_id, action_key="pdf.download"
    )
    content_service = ContentService(session)
    return content_service.get_content_download_url(
        node_id, user.organization_id
    )


@router.post(
    "/export-rst",
    summary="Export Markdown content to RST and return the file",
)
def export_markdown_content_to_rst(
    session: CurrentSession,
    user: UserToken,  # for consistency with other endpoints, validate token here...
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
