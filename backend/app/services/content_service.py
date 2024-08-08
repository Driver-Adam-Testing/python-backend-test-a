from fastapi import HTTPException

from app.repositories.content_repository import ContentRepository
from sqlmodel import Session

from app.schemas.content_schema import (
    CreateContentResponse,
    CreateTemplateResponse,
    ListContentInput,
    ListContentResults,
    ListContentResult,
    ListContentTypesInput,
    ListContentTypesResults,
)

from app.api.session import CurrentSession


class ContentService:
    def __init__(self, session: Session):
        self.content_repository = ContentRepository(session)

    def create_blank_document(self, organization_id: str, workspace_id: str, codebase_id: str) -> CreateContentResponse:
        document = self.content_repository.create_blank_document(organization_id, workspace_id, codebase_id)
        return CreateContentResponse(content_id=str(document.id))

    def create_template(self, organization_id: str, workspace_id: str, codebase_id: str) -> CreateContentResponse:
        template = self.content_repository.create_template(organization_id, workspace_id, codebase_id)
        return CreateContentResponse(content_id=template.id)

    def create_document_from_template(self, content_id: str) -> CreateContentResponse:
        document = self.content_repository.create_document_from_template(content_id)
        return CreateContentResponse(content_id=document.id)

    def get_list_content(self, organization_id: str, search_input: ListContentInput) -> ListContentResults:

        try:
            results, total_count = self.content_repository.get_list_content(organization_id, search_input)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        # format the results
        content_results = [
            ListContentResult(
                id=result.id,
                organization_id=organization_id,
                content_type_id=result.content_type_id,
                content_type_name=result.content_type.type_name,
                workspace_id=result.workspace_id,
                workspace_name=result.workspace.display_name,
                source_content_id=result.source_content_id,
                codebase_id=result.codebase_id,
                relative_path=result.relative_path,
                content=result.content,
                misc_metadata=result.misc_metadata,
                status=result.status,
                created_at=result.created_at,
                updated_at=result.updated_at,
                source_content=result.source_content,
                order=result.order,
                tags=result.tags,
            )
            for result in results
        ]
        return ListContentResults(
            results=content_results,
            offset=search_input.offset,
            limit=search_input.limit,
            count=total_count,
        )

    def get_list_content_types(self, lct_inputs: ListContentTypesInput) -> ListContentTypesResults:
        try:
            results = self.content_repository.get_content_types(
                lct_inputs.limit,
                lct_inputs.offset,
                lct_inputs.sort_by,
                lct_inputs.sort_direction
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return ListContentTypesResults(results=results)


def get_content_service(session: CurrentSession) -> ContentService:
    return ContentService(session=session)
