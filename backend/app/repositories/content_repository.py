import json
from datetime import datetime
from typing import Sequence, Optional

from app.repositories.base_repository import BaseRepository
from app.schemas.content_schema import ListContentInput, ListContentResults, ListContentResult
from sqlmodel import Session, asc, desc, or_, select, func

from sqlalchemy.exc import NoResultFound
from database.models_v1 import (
    DerivedContent,
    DerivedContentType,
    Workspace,
    Enum_Derived_Content_Status,
    Tag,
    TagContent
)


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self, session: Session):
        super().__init__(session, Workspace)

    def exists(self, id: str, organization_id: str) -> bool:
        workspace = self.get(id)
        if not workspace:
            return False
        return workspace.organization_id == organization_id


class DerivedContentTypeRepository(BaseRepository[DerivedContentType]):
    def __init__(self, session: Session):
        super().__init__(session, DerivedContentType)

    def get_by_type_name(self, type_name: str) -> DerivedContentType:
        return self.session.exec(
            select(DerivedContentType)
            .where(DerivedContentType.type_name == type_name)
        ).first()


class ContentRepository(BaseRepository[DerivedContent]):
    def __init__(self, session: Session):
        super().__init__(session, DerivedContent)
        # self.session = session
        self.derived_content_type_repository = DerivedContentTypeRepository(session)
        self.workspace_repository = WorkspaceRepository(session)

    def create_blank_document(
            self,
            organization_id: str,
            workspace_id: str,
            codebase_id: str,
            document_name: str | None = None) -> DerivedContent:
        workspace_exists = self.workspace_repository.exists(workspace_id, organization_id)

        if not workspace_exists:
            raise NoResultFound("Workspace not found")

            # get application note derived content type
        application_note_content_type = self.derived_content_type_repository.get_by_type_name("application_note")

        # get codebase derived content type
        codebase_content_type = self.derived_content_type_repository.get_by_type_name("codebase")

        # find the derived content type with content type codebase and workspace id and codebase id
        parent_content = self.session.exec(
            select(DerivedContent)
            .where(DerivedContent.content_type_id == codebase_content_type.id)
            .where(DerivedContent.workspace_id == workspace_id)
            .where(DerivedContent.codebase_id == codebase_id)
        ).first()

        blank_content_template = {
            "name": "Untitled" if document_name is None else document_name,
            "content": " ",
            "description": ""
        }

        new_content = self.create(DerivedContent(
            content_type_id=application_note_content_type.id,
            workspace_id=workspace_id,
            source_content_id=parent_content.id,
            codebase_id=codebase_id,
            relative_path=parent_content.relative_path,
            content=json.dumps(blank_content_template),
            misc_metadata={},
            status=Enum_Derived_Content_Status.generation_complete,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ))

        return new_content

    def create_template(self, organization_id: str, workspace_id: str, codebase_id: str) -> DerivedContent:
        workspace_exists = self.workspace_repository.exists(workspace_id, organization_id)

        if not workspace_exists:
            raise NoResultFound("Workspace not found")

        # get application note derived content type
        template_content_type = self.derived_content_type_repository.get_by_type_name("template")

        # get codebase derived content type
        codebase_content_type = self.derived_content_type_repository.get_by_type_name("codebase")

        # find the derived content type with content type codebase and workspace id and codebase id
        parent_content = self.session.exec(
            select(DerivedContent)
            .where(DerivedContent.content_type_id == codebase_content_type.id)
            .where(DerivedContent.workspace_id == workspace_id)
            .where(DerivedContent.codebase_id == codebase_id)
        ).first()

        blank_content_template = {
            "name": "Template",
            "content": " ",
            "description": ""
        }
        # Add the new content to the session and commit
        new_content = self.create(DerivedContent(
            content_type_id=template_content_type.id,
            workspace_id=workspace_id,
            source_content_id=parent_content.id,
            codebase_id=codebase_id,
            relative_path=parent_content.relative_path,
            content=json.dumps(blank_content_template),
            misc_metadata={},
            status=Enum_Derived_Content_Status.generation_complete,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ))

        return new_content

    def create_document_from_template(self, content_id: str) -> DerivedContent:
        # get the template content type
        template_content_type = self.derived_content_type_repository.get_by_type_name("template")
        # get the content
        content = self.session.exec(
            select(DerivedContent)
            .where(DerivedContent.id == content_id)
            .where(DerivedContent.content_type_id == template_content_type.id)
        ).first()

        if not content:
            raise NoResultFound("Content not found")

        content_template = json.loads(content.content)

        # copy content_template to new_content_template
        new_content_template = content_template.copy()
        new_content_name = new_content_template["name"]
        new_content_template["name"] = f"{new_content_name} (Copy)"
        new_content_content = json.dumps(new_content_template)

        application_note_content_type = self.derived_content_type_repository.get_by_type_name("application_note")

        # create a new content from the template
        new_content = self.create(DerivedContent(
            content_type_id=application_note_content_type.id,
            workspace_id=content.workspace_id,
            source_content_id=content.source_content_id,
            codebase_id=content.codebase_id,
            relative_path=content.relative_path,
            content=new_content_content,
            misc_metadata={},
            status=Enum_Derived_Content_Status.generation_complete,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ))
        return new_content

    def get_list_content(
            self,
            organization_id: str,
            search_input: ListContentInput
    ) -> tuple[list[DerivedContent], int]:
        statement = (
            select(DerivedContent)
            .join(DerivedContentType)
            .join(Workspace)
            .join(TagContent, isouter=True)
            .join(Tag, isouter=True)
            # TODO: Current plan is for workspaces to be removed from the application.
            # In this intermediate state, we are maintaining the existing workspace
            # table and joining them all together to obtain all content that is currently
            # housed under the given organization. This will need updated if/when the
            # workspace data is being migrated.
            .where(organization_id == Workspace.organization_id)
        )
        count_statement = (
            select(func.count())
            .select_from(DerivedContent)
            .join(DerivedContentType)
            .join(Workspace)
            .join(TagContent, isouter=True)
            .join(Tag, isouter=True)
            .where(organization_id == Workspace.organization_id)
        )
        if search_input.sort_by:
            if search_input.sort_direction == "ASC":
                statement = statement.order_by(asc(search_input.sort_by))
            elif search_input.sort_direction == "DESC":
                statement = statement.order_by(desc(search_input.sort_by))
            else:
                raise ValueError("Invalid sort direction provided. Options are ASC or DESC")

        if search_input.text:
            statement = statement.where(DerivedContent.relative_path.contains(search_input.text))
            count_statement = count_statement.where(
                DerivedContent.relative_path.contains(search_input.text)
            )

        if search_input.status:
            statement = statement.where(DerivedContent.status == search_input.status)
            count_statement = count_statement.where(DerivedContent.status == search_input.status)

        if search_input.content_type_id:
            statement = statement.where(
                DerivedContent.content_type_id.in_(search_input.content_type_id)
            )
            count_statement = count_statement.where(
                DerivedContent.content_type_id.in_(search_input.content_type_id)
            )

        if search_input.content_type_name:
            statement = statement.where(
                DerivedContentType.type_name.in_(search_input.content_type_name)
            )
            count_statement = count_statement.where(
                DerivedContentType.type_name.in_(search_input.content_type_name)
            )

        if search_input.tags:
            tag_clauses = []
            for tag in search_input.tags:
                tag_clauses.append(Tag.name.contains(tag))
            statement = statement.where(or_(*tag_clauses))
            count_statement = count_statement.where(or_(*tag_clauses))

        if search_input.tag_ids:
            tag_id_clauses = []
            for tag_id in search_input.tag_ids:
                tag_id_clauses.append(Tag.id == tag_id)
            statement = statement.where(or_(*tag_id_clauses))
            count_statement = count_statement.where(or_(*tag_id_clauses))

        total_count = self.session.exec(count_statement).one()
        results = self.session.exec(statement.offset(search_input.offset).limit(search_input.limit)).all()
        return results, total_count

    def get_content_types(
            self,
            limit: int = 100,
            offset: int = 0,
            sort_by: Optional[str] = None,
            sort_direction: str = "DESC"
    ) -> list[DerivedContentType]:
        return self.derived_content_type_repository.get_all(limit, offset, sort_by, sort_direction)
