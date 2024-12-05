from fastapi import APIRouter

from app.api.auth import ContentEditorPermission, UserToken
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.upload_schema import (
    AnalyzeCodebaseUploadResponse,
    PDFUploadResponse,
    UploadCodebaseRequest,
    UploadPDFRequest,
    UploadResponse,
)
from app.services.upload_service import UploadService

router = APIRouter()


@router.post(
    "/codebase", summary="Upload a codebase", dependencies=[ContentEditorPermission]
)
def upload_codebase(
    session: CurrentSession,
    user: UserToken,
    request: UploadCodebaseRequest,
) -> UploadResponse:
    """Upload a codebase."""
    logger.info(f"upload_codebase called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.upload_codebase(user, request)


@router.post("/pdf", summary="Upload a pdf", dependencies=[ContentEditorPermission])
def upload_pdf(
    session: CurrentSession,
    user: UserToken,
    request: UploadPDFRequest,
) -> PDFUploadResponse:
    """Upload a codebase."""
    logger.info(f"upload_codebase called with request: {request}")
    upload_service = UploadService(session)
    return upload_service.upload_pdf(user, request)


@router.post(
    "/analyze/codebase",
    summary="Upload and analyze a codebase",
    dependencies=[ContentEditorPermission],
)
def upload_analyze_codebase(
    session: CurrentSession, user: UserToken, request: UploadCodebaseRequest
) -> AnalyzeCodebaseUploadResponse:
    """
    1. Generate presigned put URL for the codebase
    2. Generate presigned get URL for the codebase
    3. return the presigned put and get URL
    """
    upload_service = UploadService(session)
    return upload_service.upload_analyze_codebase(user, request)
