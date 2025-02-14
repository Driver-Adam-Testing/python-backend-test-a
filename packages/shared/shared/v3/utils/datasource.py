from uuid import UUID

from database.db import get_session
from database.models_v1 import DocumentSource
from pydantic import BaseModel
from sqlmodel import select


class DataSource(BaseModel):
    node_ids: list[UUID]
    organization_id: str

    @classmethod
    def from_node_ids(cls, node_ids: list[UUID], organization_id: str) -> "DataSource":
        return cls(node_ids=node_ids, organization_id=organization_id)

    @classmethod
    def from_page_id(cls, page_node_id: UUID, organization_id: str) -> "DataSource":
        with get_session() as session:
            document_sources = session.exec(
                select(DocumentSource).where(
                    DocumentSource.page_node_id == page_node_id
                )
            ).all()
            return cls(
                node_ids=[
                    document_source.source_node_id
                    for document_source in document_sources
                ],
                organization_id=organization_id,
            )
