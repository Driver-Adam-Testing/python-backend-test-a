from database.models_v1 import DerivedContentType
from sqlmodel import Session, select

from app.core.logger import logger
from app.repositories.base_repository import BaseRepository


class DerivedContentTypeRepository(BaseRepository[DerivedContentType]):
    def __init__(self, session: Session):
        super().__init__(session, DerivedContentType)

    def get_by_type_name(self, type_name: str) -> DerivedContentType:
        logger.info(f"Fetching DerivedContentType by type_name: {type_name}")
        return self.session.exec(
            select(DerivedContentType).where(DerivedContentType.type_name == type_name)
        ).first()

    def get_by_type_names(self, type_names: list[str]) -> DerivedContentType:
        logger.info(f"Fetching DerivedContentType by type_names: {type_names}")
        return self.session.exec(
            select(DerivedContentType).where(
                DerivedContentType.type_name.in_(type_names)
            )
        ).first()

    @staticmethod
    def valid_collection_type_names() -> list[str]:
        return [
            "codebase",
            "codebase-directory",
            "codebase-file",
            "pdf_summary",
            "supplemental-document",
        ]
