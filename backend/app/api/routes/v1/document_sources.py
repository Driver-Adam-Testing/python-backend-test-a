from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.services.document_source_service import DocumentSourceService
from app.schemas.document_source_schema import DocumentSourceCreate
from app.api.auth import CurrentUser
from app.api.session import CurrentSession
router = APIRouter()

@router.post("/")
def create_document_source(
    session: CurrentSession,
    user: CurrentUser,
    document_source_create: DocumentSourceCreate,
):
    document_source_service = DocumentSourceService(session)
    return document_source_service.create_document_source(document_source_create)


@router.get("/{document_id}/{source_id}")
def get_document_source(
    session: CurrentSession,
    user: CurrentUser,
    document_id: UUID,
    source_id: UUID,
):
    document_source_service = DocumentSourceService(session)
    document_source = document_source_service.get_document_source(document_id, source_id)
    if not document_source:
        raise HTTPException(status_code=404, detail="Document source not found")
    return document_source


@router.delete("/{document_id}/{source_id}")
def delete_document_source(
    session: CurrentSession,
    user: CurrentUser,
    document_id: UUID,
    source_id: UUID,
):
    document_source_service = DocumentSourceService(session)
    return document_source_service.delete_document_source(document_id, source_id)