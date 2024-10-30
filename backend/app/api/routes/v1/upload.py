from fastapi import APIRouter

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.upload_schema import (
    PDFUploadResponse,
    UploadCodebaseRequest,
    UploadPDFRequest,
    UploadResponse,
)
from app.services.upload_service import UploadService

router = APIRouter()


@router.post("/codebase", summary="Upload a codebase")
def upload_codebase(
    session: CurrentSession,
    user: UserToken,
    request: UploadCodebaseRequest,
) -> UploadResponse:
    """Upload a codebase."""
    logger.info(f"upload_codebase called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.upload_codebase(user, request)


@router.post("/pdf", summary="Upload a pdf")
def upload_pdf(
    session: CurrentSession,
    user: UserToken,
    request: UploadPDFRequest,
) -> PDFUploadResponse:
    """Upload a codebase."""
    logger.info(f"upload_codebase called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.upload_pdf(user, request)
