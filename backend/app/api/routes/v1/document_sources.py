from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession
from app.schemas.document_source_schema import DocumentSourceCreate
from app.services.document_source_service import DocumentSourceService

router = APIRouter()


@router.post("/", dependencies=[ContentEditorPermission])
def create_document_source(
    session: CurrentSession,
    user: UserToken,
    document_source_create: DocumentSourceCreate,
):
    document_source_service = DocumentSourceService(session)
    return document_source_service.create_document_source(document_source_create)


@router.get("/{document_id}/{source_id}", dependencies=[ContentReadonlyPermission])
def get_document_source(
    session: CurrentSession,
    user: UserToken,
    document_id: UUID,
    source_id: UUID,
):
    document_source_service = DocumentSourceService(session)
    document_source = document_source_service.get_document_source(
        document_id, source_id
    )
    if not document_source:
        raise HTTPException(status_code=404, detail="Document source not found")
    return document_source


@router.delete("/{document_id}/{source_id}", dependencies=[ContentEditorPermission])
def delete_document_source(
    session: CurrentSession,
    user: UserToken,
    document_id: UUID,
    source_id: UUID,
):
    document_source_service = DocumentSourceService(session)
    return document_source_service.delete_document_source(document_id, source_id)
