from fastapi import APIRouter

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.upload_schema import (
    UploadCodebaseRequest,
    UploadPDFRequest,
    UploadResponse,
)
from app.services.upload_service import UploadService

router = APIRouter()


@router.post("/codebase", summary="Upload a codebase")
def upload_codebase(
    session: CurrentSession,
    user: CurrentUser,
    request: UploadCodebaseRequest,
) -> UploadResponse:
    """Upload a codebase."""
    logger.info(f"upload_codebase called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.upload_codebase(user, request)


@router.post("/pdf", summary="Upload a pdf")
def upload_pdf(
    session: CurrentSession,
    user: CurrentUser,
    request: UploadPDFRequest,
) -> UploadResponse:
    """Upload a codebase."""
    logger.info(f"upload_codebase called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.upload_pdf(user, request)
