from fastapi import APIRouter

from app.api.auth import ContentEditorPermission, UserToken
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.upload_schema import (
    UploadAutoDocConfigRequest,
    UploadAutoDocConfigResponse,
    UploadRequest,
    UploadResponse,
)
from app.services.upload_service import UploadService

router = APIRouter()


@router.post(
    "/",
    summary="Create upload URL",
    dependencies=[ContentEditorPermission],
)
def create_upload_url(
    session: CurrentSession,
    user: UserToken,
    request: UploadRequest,
) -> UploadResponse:
    """Upload a zip or pdf."""
    logger.info(f"create_upload_url called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.create_asset_version_and_upload_url(user, request)


@router.post(
    "/config",
    summary="Create upload URL for a custom config",
    dependencies=[ContentEditorPermission],
)
def create_upload_url_for_custom_config(
    session: CurrentSession,
    user: UserToken,
    request: UploadAutoDocConfigRequest,
) -> UploadAutoDocConfigResponse:
    """Upload a custom config."""
    logger.info(f"create_upload_url_for_custom_config called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.create_custom_config_and_upload_url(user, request)
