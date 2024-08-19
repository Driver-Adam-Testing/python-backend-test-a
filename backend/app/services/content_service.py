import json
import logging
from datetime import datetime

from database.models_v1 import (
    DerivedContent,
    DerivedContentType,
    DocumentSource,
    Enum_Derived_Content_Status,
    Tag,
    TagContent,
    Workspace,
)
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import Session, asc, desc, func, or_, select, text

from app.api.session import CurrentSession
from app.repositories.base_repository import BaseRepository
from app.schemas.content_schema import (
    ListContentInput,
    ListContentResult,
    ListContentResults,
    ListContentTypesInput,
    ListContentTypesResults,
    TagAssociationResponse,
)

logger = logging.getLogger(__name__)


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


class ContentService:
    def __init__(self, session: Session):
        self.session = session
        self.content_repository = BaseRepository(session, DerivedContent)
        self.workspace_repository = BaseRepository(session, Workspace)
        self.tag_repository = BaseRepository(session, Tag)
        self.derived_content_type_repository = DerivedContentTypeRepository(session)

    def associate_tag(
        self,
        organization_id: str,
        content_id: str,
        tag_id: str,
        include_tag: bool = True,
    ) -> TagAssociationResponse:
        logger.info(
            f"Associating tag {tag_id} with content {content_id} for organization {organization_id}"
        )
        # Check if content exists
        content = self.content_repository.get_by_conditions(
            [
                organization_id == Workspace.organization_id,
                DerivedContent.id == content_id,
            ],
            [Workspace],
        )

        if not content:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found.",
            )

        # Check if tag exists
        tag = self.tag_repository.get_by_conditions(
            [Tag.id == tag_id, Tag.organization_id == organization_id]
        )

        if not tag:
            logger.error(f"Tag {tag_id} not found for organization {organization_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found.",
            )

        if tag.type == "collection":
            if (
                content.content_type.type_name
                not in DerivedContentTypeRepository.valid_collection_type_names()
            ):
                logger.error(
                    f"Invalid content type for collection tag {tag_id} and content {content_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Collections can only be associated with codebases, directories, files or pdfs.",
                )

        include_tag = (
            include_tag
            if include_tag is not None and tag.type == "collection"
            else True
        )
        # Associate tag with content
        content.tag_links.append(
            TagContent(tag_id=tag.id, content_id=content.id, include=include_tag)
        )

        try:
            self.session.commit()
            logger.info(
                f"Tag {tag_id} associated with content {content_id} successfully"
            )
        except IntegrityError:
            self.session.rollback()
            logger.error(
                f"Integrity error while associating tag {tag_id} with content {content_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag association already exists",
            )

        return TagAssociationResponse(
            tag_id=tag_id,
            content_id=content_id,
            message=f"{tag.type} associated successfully",
        )

    def associate_collection_with_content(
        self, organization_id: str, content_id: str, tag_id: str
    ) -> TagAssociationResponse:
        logger.info(
            f"Associating collection tag {tag_id} with content {content_id} for organization {organization_id}"
        )
        document = self.content_repository.get(content_id)

        if not document or document.workspace.organization_id != organization_id:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )
        # get the content source content related to the tag_id
        tag_contents = self.session.exec(
            select(TagContent).where(TagContent.tag_id == tag_id)
        ).all()

        # source_contents = [tag_content.content for tag_content in tag_contents]

        sources = [
            DocumentSource(
                document_id=content_id,
                source_id=tag_content.content_id,
                include=tag_content.include,
            )
            for tag_content in tag_contents
        ]

        for source in sources:
            document.source_links.append(source)

        try:
            self.session.commit()
            logger.info(
                f"Collection tag {tag_id} associated with content {content_id} successfully"
            )
        except IntegrityError:
            self.session.rollback()
            logger.error(
                f"Integrity error while associating collection tag {tag_id} with content {content_id}"
            )
            # raise HTTPException(
            #     status_code=status.HTTP_400_BAD_REQUEST,
            #     detail="Integrity error occurred while associating collection with content",
            # )

        return TagAssociationResponse(
            tag_id=tag_id,
            content_id=content_id,
            message="Collection associated successfully",
        )

    def disassociate_tag(
        self, organization_id: str, content_id: str, tag_id: str
    ) -> TagAssociationResponse:
        logger.info(
            f"Disassociating tag {tag_id} from content {content_id} for organization {organization_id}"
        )
        # Check if content exists

        content = self.session.exec(
            select(DerivedContent)
            .join(Workspace)
            .join(DerivedContent.tags)
            .where(organization_id == Workspace.organization_id)
            .where(DerivedContent.id == content_id)
        ).first()

        if not content:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )
        # Check if tag exists
        tag = self.session.exec(
            select(Tag)
            .where(Tag.id == tag_id)
            .where(organization_id == Tag.organization_id)
        ).first()

        if not tag:
            logger.error(f"Tag {tag_id} not found for organization {organization_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )

        # Disassociate tag with content
        link = self.session.exec(
            select(TagContent)
            .where(TagContent.tag_id == tag_id)
            .where(TagContent.content_id == content_id)
        ).first()

        if link is None:
            logger.error(
                f"Tag association not found for tag {tag_id} and content {content_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag association not found",
            )

        if link:
            self.session.delete(link)
            self.session.commit()
            logger.info(
                f"Tag {tag_id} disassociated from content {content_id} successfully"
            )
            return TagAssociationResponse(
                tag_id=tag_id,
                content_id=content_id,
                message="Tag disassociated successfully",
            )

    def create_blank_document(
        self,
        organization_id: str,
        workspace_id: str,
        codebase_id: str,
        document_name: str | None = None,
    ) -> DerivedContent:
        logger.info(
            f"Creating blank document for organization {organization_id}, workspace {workspace_id}, codebase {codebase_id}"
        )
        workspace_exists = self.workspace_repository.exists(
            workspace_id, organization_id
        )

        if not workspace_exists:
            logger.error(
                f"Workspace {workspace_id} not found for organization {organization_id}"
            )
            raise NoResultFound("Workspace not found")

        # get application note derived content type
        application_note_content_type = (
            self.derived_content_type_repository.get_by_type_name("application_note")
        )

        # get codebase derived content type
        codebase_content_type = self.derived_content_type_repository.get_by_type_name(
            "codebase"
        )

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
            "description": "",
        }

        new_content = self.content_repository.create(
            DerivedContent(
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
            )
        )
        logger.info(
            f"Blank document created with ID {new_content.id} for organization {organization_id}"
        )
        return new_content

    def create_document_from_template(
        self, organization_id: str, content_id: str
    ) -> DerivedContent:
        logger.info(
            f"Creating document from template for organization {organization_id}, content {content_id}"
        )
        # get the template content type
        template_content_type = self.derived_content_type_repository.get_by_type_name(
            "template"
        )
        # get the content
        content = self.session.exec(
            select(DerivedContent)
            .where(DerivedContent.id == content_id)
            .where(DerivedContent.content_type_id == template_content_type.id)
        ).first()

        if not content:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise NoResultFound("Content not found")

        content_template = json.loads(content.content)

        # copy content_template to new_content_template
        new_content_template = content_template.copy()
        new_content_name = new_content_template["name"]
        new_content_template["name"] = f"{new_content_name} (Copy)"
        new_content_content = json.dumps(new_content_template)

        application_note_content_type = (
            self.derived_content_type_repository.get_by_type_name("application_note")
        )

        # create a new content from the template
        new_content = self.content_repository.create(
            DerivedContent(
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
            )
        )
        logger.info(
            f"Document created from template with ID {new_content.id} for organization {organization_id}"
        )
        return new_content

    def get_list_content(
        self, organization_id: str, search_input: ListContentInput
    ) -> ListContentResults:
        logger.info(
            f"Getting list of content for organization {organization_id} with input {search_input}"
        )
        try:
            results, total_count = self._get_list_content(organization_id, search_input)
        except ValueError as e:
            logger.error(
                f"Error getting list of content for organization {organization_id}: {str(e)}"
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        # format the results
        content_results = [
            ListContentResult(
                id=result.id,
                organization_id=result.workspace.organization_id,
                content_type_id=result.content_type_id,
                content_type_name=result.content_type.type_name,
                content_name=(
                    json.loads(result.content).get("name")
                    if result.content_type.type_name == "application_note"
                    and result.content
                    and "name" in json.loads(result.content)
                    else "Generating content..."
                    if result.content_type.type_name == "application_note"
                    and result.content
                    and "name" not in json.loads(result.content)
                    else result.relative_path.removeprefix("documents/")
                    if result.content_type.type_name == "supplemental-document"
                    else result.relative_path
                ),
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
                source_links=result.source_links,
                # tags=[tag_link.tag for tag_link in result.tag_links],
            )
            for result in results
        ]
        logger.info(
            f"List of content retrieved successfully for organization {organization_id}"
        )
        return ListContentResults(
            results=content_results,
            offset=search_input.offset,
            limit=search_input.limit,
            count=total_count,
        )

    def _get_list_content(
        self, organization_id: str, search_input: ListContentInput
    ) -> tuple[list[DerivedContent], int]:
        statement = (
            select(DerivedContent)
            .join(DerivedContentType)
            .join(Workspace)
            .join(TagContent, isouter=True)
            .join(Tag, isouter=True)
            .join(
                DocumentSource,
                isouter=True,
                onclause=DerivedContent.id == DocumentSource.document_id,
            )
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
            if not hasattr(self.content_repository.model, search_input.sort_by):
                raise ValueError(
                    f"Invalid sort field '{search_input.sort_by}' for model '{self.content_repository.model.__tablename__}'."
                )

            field_name = (
                f"{self.content_repository.model.__tablename__}.{search_input.sort_by}"
            )
            if search_input.sort_direction == "ASC":
                statement = statement.order_by(asc(text(field_name)))
            elif search_input.sort_direction == "DESC":
                statement = statement.order_by(desc(text(field_name)))
            else:
                raise ValueError(
                    "Invalid sort direction provided. Options are ASC or DESC"
                )

        if search_input.text:
            statement = statement.where(
                DerivedContent.relative_path.contains(search_input.text)
            )
            count_statement = count_statement.where(
                DerivedContent.relative_path.contains(search_input.text)
            )

        if search_input.status:
            statement = statement.where(DerivedContent.status == search_input.status)
            count_statement = count_statement.where(
                DerivedContent.status == search_input.status
            )

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
        results = self.session.exec(
            statement.offset(search_input.offset).limit(search_input.limit)
        ).all()
        return results, total_count

    def get_list_content_types(
        self, lct_inputs: ListContentTypesInput
    ) -> ListContentTypesResults:
        logger.info(f"Getting list of content types with input {lct_inputs}")
        try:
            results = self.derived_content_type_repository.get_all(
                lct_inputs.limit,
                lct_inputs.offset,
                lct_inputs.sort_by,
                lct_inputs.sort_direction,
            )
        except ValueError as e:
            logger.error(f"Error getting list of content types: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        logger.info("List of content types retrieved successfully")
        return ListContentTypesResults(results=results)

    def resolve_content_sources(self, content_id: str) -> list[DerivedContent]:
        logger.info(f"Resolving content sources for content {content_id}")
        content = self.content_repository.get(content_id)
        if not content:
            logger.error(f"Content {content_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        sources = [link.source for link in content.source_links]

        for source in sources:
            # resolve codebase content
            if source.content_type.type_name == "codebase":
                pass
            # resolve codebase-directory content
            elif source.content_type.type_name == "codebase-directory":
                pass
            # resolve codebase-file content
            elif source.content_type.type_name == "codebase-file":
                pass
            # resolve pdf_summary content
            elif source.content_type.type_name == "pdf_summary":
                pass
            # resolve supplemental-document content
            elif source.content_type.type_name == "supplemental-document":
                pass
            else:
                pass

        logger.info(f"Content sources resolved for content {content_id}")
        return sources

    def create_template(
        self, organization_id: str, workspace_id: str, codebase_id: str
    ) -> DerivedContent:
        logger.info(
            f"Creating template for organization {organization_id}, workspace {workspace_id}, codebase {codebase_id}"
        )
        workspace_exists = self.workspace_repository.exists(
            workspace_id, organization_id
        )

        if not workspace_exists:
            logger.error(
                f"Workspace {workspace_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
            )

        # get application note derived content type
        template_content_type = self.derived_content_type_repository.get_by_type_name(
            "template"
        )

        # get codebase derived content type
        codebase_content_type = self.derived_content_type_repository.get_by_type_name(
            "codebase"
        )

        # find the derived content type with content type codebase and workspace id and codebase id
        parent_content = self.session.exec(
            select(DerivedContent)
            .where(DerivedContent.content_type_id == codebase_content_type.id)
            .where(DerivedContent.workspace_id == workspace_id)
            .where(DerivedContent.codebase_id == codebase_id)
        ).first()

        blank_content_template = {"name": "Template", "content": " ", "description": ""}
        # Add the new content to the session and commit
        new_content = self.content_repository.create(
            DerivedContent(
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
            )
        )
        logger.info(
            f"Template created with ID {new_content.id} for organization {organization_id}"
        )
        return new_content


def get_content_service(session: CurrentSession) -> ContentService:
    return ContentService(session=session)
