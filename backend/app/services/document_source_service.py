from database.models_v1 import DocumentSource
from app.repositories.base_repository import BaseRepository
from app.schemas.document_source_schema import DocumentSourceCreate
from fastapi import HTTPException


class DocumentSourceService:
    def __init__(self, session):
        self.session = session
        self.document_source_repository = BaseRepository(session, DocumentSource)

    def get_document_source(self, document_id, source_id):
        return self.document_source_repository.get_by_pk(document_id=document_id, source_id=source_id)

    def create_document_source(self, document_source_create: DocumentSourceCreate):
        document_source_data = document_source_create.model_dump()
        document_id = document_source_data['document_id']
        source_id = document_source_data['source_id']

        existing_document_source = self.get_document_source(document_id, source_id)
        if existing_document_source:
            raise HTTPException(status_code=400, detail="Document source already exists")

        document_source_instance = DocumentSource(**document_source_data)

        return self.document_source_repository.create(document_source_instance)

    # def update_document_source(self, document_id, source_id):
    #     return self.document_source_repository.update(document_id=document_id, source_id=source_id)

    def delete_document_source(self, document_id, source_id):
        return self.document_source_repository.delete_by_pk(document_id=document_id, source_id=source_id)
