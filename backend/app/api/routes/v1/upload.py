import logging

from fastapi import APIRouter

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_org_action
from app.schemas.upload_schema import (
    UploadAutoDocConfigRequest,
    UploadAutoDocConfigResponse,
    UploadRequest,
    UploadResponse,
)
from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    summary="Create upload URL",
)
def create_upload_url(
    session: CurrentSession,
    user: UserToken,
    request: UploadRequest,
) -> UploadResponse:
    """Upload a zip or pdf."""
    enforce_org_action(db=session, user=user, action_key="asset.upload")
    logger.info(f"create_upload_url called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.create_asset_version_and_upload_url(user, request)


@router.post(
    "/config",
    summary="Create upload URL for a custom config",
)
def create_upload_url_for_custom_config(
    session: CurrentSession,
    user: UserToken,
    request: UploadAutoDocConfigRequest,
) -> UploadAutoDocConfigResponse:
    """Upload a custom config."""
    # TODO: remove this endpoint?
    enforce_org_action(db=session, user=user, action_key="autodoc.custom_config_upload")
    logger.info(f"create_upload_url_for_custom_config called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.create_custom_config_and_upload_url(user, request)
