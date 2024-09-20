import json
from datetime import datetime
from uuid import UUID

from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import (
    Codebase,
    DerivedContent,
    DerivedContentType,
    DocumentSource,
    Enum_Derived_Content_Status,
    Tag,
    TagContent,
    Workspace,
)
from fastapi import HTTPException, status
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, asc, desc, func, or_, select, text

from app.core.logger import logger
from app.repositories.base_repository import BaseRepository
from app.repositories.derived_content_type_repository import (
    DerivedContentTypeRepository,
)
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.content_schema import (
    BatchContentSourceAssociationResponse,
    ContentSourceAssociationItem,
    ContentSourceAssociationResponse,
    ContentSourceResponse,
    CreateContentRequest,
    DeleteDocumentSourceResponse,
    DownloadContentResponse,
    ListContentInput,
    ListContentResult,
    ListContentResults,
    ListContentTypesInput,
    ListContentTypesResults,
)
from app.services.utils.content_utils import get_content_name
from app.utils import aws_s3
from app.utils.authorization_chain import perform_authorization_checks


def is_authorized(
    session: Session, user_org_id: str, workspace_id: UUID, codebase_id: UUID
) -> bool:
    # Check if the workspace belongs to the organization
    workspace = session.exec(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.organization_id == user_org_id
        )
    ).first()

    if not workspace:
        return False

    # Check if the codebase belongs to the workspace
    codebase = session.exec(
        select(Codebase).where(
            Codebase.id == codebase_id, Codebase.workspace_id == workspace_id
        )
    ).first()

    return codebase


class ContentService:
    def __init__(self, session: Session):
        self.session = session
        self.content_repository = BaseRepository(session, DerivedContent)
        self.workspace_repository = WorkspaceRepository(session)
        self.derived_content_type_repository = DerivedContentTypeRepository(session)
        self.document_source_repository = BaseRepository(session, DocumentSource)

    def associate_sources_with_content(
        self,
        organization_id: str,
        content_id: UUID,
        content_source_associations: list[ContentSourceAssociationItem],
    ) -> BatchContentSourceAssociationResponse:
        logger.info(
            f"Associating {len(content_source_associations)} sources with content {content_id} for organization {organization_id}"
        )

        checks = [
            lambda session: self.content_repository.is_authorized(
                id=content_id,
                relationship_chain=["workspace"],
                field_name="organization_id",
                field_value=organization_id,
            )
        ]

        perform_authorization_checks(self.session, checks)

        document = self.content_repository.get(content_id)

        if not document or document.workspace.organization_id != organization_id:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        existing_sources = self.session.exec(
            select(DocumentSource).where(DocumentSource.document_id == content_id)
        ).all()

        incoming_source_ids = {
            source.source_content_id for source in content_source_associations
        }
        for source in content_source_associations:
            if not self.content_repository.exists(source.source_content_id):
                logger.error(f"Source content {source.source_content_id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source content not found",
                )

        for existing_source in existing_sources:
            if existing_source.source_id not in incoming_source_ids:
                self.session.delete(existing_source)

        for source in content_source_associations:
            self.session.merge(
                DocumentSource(
                    document_id=content_id,
                    source_id=source.source_content_id,
                    include=source.include,
                )
            )

        self.session.commit()

        logger.info(
            f"Source content association with content {content_id} successfully updated"
        )

        return BatchContentSourceAssociationResponse(
            content_id=content_id,
            sources=content_source_associations,
            message="Source content associated successfully",
        )

    def associate_document_source(
        self,
        organization_id: str,
        content_id: UUID,
        source_id: UUID,
        include: bool = True,
    ) -> ContentSourceAssociationResponse:
        logger.info(
            f"Associating content {content_id} with {source_id} for organization {organization_id}"
        )

        checks = [
            lambda session: self.content_repository.is_authorized(
                id=content_id,
                relationship_chain=["workspace"],
                field_name="organization_id",
                field_value=organization_id,
            )
        ]

        perform_authorization_checks(self.session, checks)

        document = self.content_repository.get(content_id)

        if not document or document.workspace.organization_id != organization_id:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        existing_document_source = self.document_source_repository.get_by_pk(
            document_id=content_id, source_id=source_id
        )
        if existing_document_source:
            raise HTTPException(
                status_code=400, detail="Document source already exists"
            )

        document_source = self.document_source_repository.create(
            DocumentSource(document_id=content_id, source_id=source_id, include=include)
        )

        return ContentSourceAssociationResponse(
            content_id=str(document_source.document_id),
            source_id=str(document_source.source_id),
            message="Source content associated successfully",
        )

    def disassociate_document_source(
        self, organization_id: str, content_id: UUID, source_content_id: UUID
    ) -> DeleteDocumentSourceResponse:
        logger.info(
            f"Disassociating source {source_content_id} from content {content_id} for organization {organization_id}"
        )

        checks = [
            lambda session: self.content_repository.is_authorized(
                id=content_id,
                relationship_chain=["workspace"],
                field_name="organization_id",
                field_value=organization_id,
            )
        ]

        perform_authorization_checks(self.session, checks)

        content = self.content_repository.get(content_id)
        if not content:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        deleted_item = self.document_source_repository.delete_by_pk(
            document_id=content_id, source_id=source_content_id
        )

        if not deleted_item:
            logger.error(
                f"Source {source_content_id} not found for content {content_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document Source not found",
            )

        return DeleteDocumentSourceResponse(
            document_id=deleted_item.document_id,
            source_id=deleted_item.source_id,
            message="Document source disassociated successfully",
        )

    def create_blank_document(
        self,
        organization_id: str,
        workspace_id: UUID,
        codebase_id: UUID,
        document_name: str | None = None,
    ) -> DerivedContent:
        logger.info(
            f"Creating blank document for organization {organization_id}, workspace {workspace_id}, codebase {codebase_id}"
        )

        checks = [
            lambda session: self.workspace_repository.is_authorized(
                id=workspace_id,
                field_name="organization_id",
                field_value=organization_id,
            )
        ]

        perform_authorization_checks(self.session, checks)

        workspace_exists = self.workspace_repository.exists(
            workspace_id, organization_id
        )

        if not workspace_exists:
            logger.error(
                f"Workspace {workspace_id} not found for organization {organization_id}"
            )
            raise NoResultFound("Workspace not found")

        application_note_content_type = (
            self.derived_content_type_repository.get_by_type_name("application_note")
        )

        codebase_content_type = self.derived_content_type_repository.get_by_type_name(
            "codebase"
        )

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

    def create_content(
        self, organization_id: str, request: CreateContentRequest
    ) -> DerivedContent:
        logger.info(
            f"Creating content for organization {organization_id} with input {request}"
        )
        # if codebase_id is None: and workspace_id is None: find the default workspace for the organization
        if request.codebase_id is not None and request.workspace_id is not None:
            return self.create_blank_document(
                organization_id, request.workspace_id, request.codebase_id
            )

        if (
            request.content_type != DerivedContentTypeNames.APPLICATION_NOTE.value
            and request.content_type != DerivedContentTypeNames.TEMPLATE.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type"
            )

        default_workspace = self.workspace_repository.get_default_workspace(
            organization_id
        )

        if not default_workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Default workspace not found",
            )

        content_type = self.derived_content_type_repository.get_by_type_name(
            request.content_type
        )

        if not content_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content type not found"
            )

        content_name = (
            "Untitled"
            if request.content_type == DerivedContentTypeNames.APPLICATION_NOTE.value
            else "Untitled Template"
        )

        new_content = self.content_repository.create(
            DerivedContent(
                content_type_id=content_type.id,
                workspace_id=default_workspace.id,
                relative_path="",
                content="",
                content_name=content_name,
                misc_metadata={},
                status=Enum_Derived_Content_Status.generation_complete,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )
        return new_content

    def create_document_from_template(
        self, organization_id: str, content_id: UUID
    ) -> DerivedContent:
        logger.info(
            f"Creating document from template for organization {organization_id}, content {content_id}"
        )

        checks = [
            lambda session: self.content_repository.is_authorized(
                id=content_id,
                relationship_chain=["workspace"],
                field_name="organization_id",
                field_value=organization_id,
            )
        ]

        perform_authorization_checks(self.session, checks)
        # TODO: add template content type
        template_content_type = self.derived_content_type_repository.get_by_type_name(
            "template"
        )
        if not template_content_type:
            logger.error("Template content type not found")
            raise NoResultFound("Template content type not found")

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
        new_content_template = content_template.copy()
        new_content_name = new_content_template["name"]
        new_content_template["name"] = f"{new_content_name} (Copy)"
        new_content_content = json.dumps(new_content_template)

        application_note_content_type = (
            self.derived_content_type_repository.get_by_type_name("application_note")
        )

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
                f"Error getting list of content for organization {organization_id}: {e!s}"
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        content_results = []
        for result in results:
            content_results.append(
                ListContentResult(
                    id=result.id,
                    organization_id=result.workspace.organization_id,
                    content_type_id=result.content_type_id,
                    content_type_name=result.content_type.type_name,
                    content_name=get_content_name(result),
                    workspace_id=result.workspace_id,
                    workspace_name=result.workspace.display_name,
                    source_content_id=result.source_content_id,
                    codebase_id=result.codebase_id,
                    codebase_name=result.codebase.codebase_name
                    if result.codebase
                    else None,
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
                )
            )
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
            .distinct()
            .join(DerivedContentType)
            .join(Workspace)
            .join(TagContent, isouter=True)
            .join(Tag, isouter=True)
            .join(
                DocumentSource,
                isouter=True,
                onclause=DerivedContent.id == DocumentSource.document_id,
            )
            .where(organization_id == Workspace.organization_id)
        )
        count_statement = (
            select(func.count(DerivedContent.id))
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
            clauses = [
                DerivedContent.relative_path.contains(search_input.text),
                DerivedContent.content_name.contains(search_input.text),
            ]
            statement = statement.where(or_(*clauses))
            count_statement = count_statement.where(or_(*clauses))

        if search_input.status:
            valid_statuses = [
                content_status.value for content_status in Enum_Derived_Content_Status
            ]
            if search_input.status not in valid_statuses:
                logger.error(f"Invalid status value: {search_input.status}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status value: {search_input.status}",
                )
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
            logger.info(
                f"Filtering by content_type_name: {search_input.content_type_name}"
            )
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
            logger.error(f"Error getting list of content types: {e!s}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        logger.info("List of content types retrieved successfully")
        return ListContentTypesResults(results=results)

    def get_content_sources(
        self, content_id: UUID, organization_id: str
    ) -> ContentSourceResponse:
        logger.info(f"Fetching content sources for content {content_id}")

        checks = [
            lambda session: self.content_repository.is_authorized(
                id=content_id,
                relationship_chain=["workspace"],
                field_name="organization_id",
                field_value=organization_id,
            )
        ]

        perform_authorization_checks(self.session, checks)

        content = self.content_repository.get(content_id)
        if not content:
            logger.error(f"Content {content_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        sources = [link.source for link in content.source_links]

        logger.info(f"Content sources resolved for content {content_id}")
        source_results = [
            ListContentResult(
                id=result.id,
                organization_id=result.workspace.organization_id,
                content_type_id=result.content_type_id,
                content_type_name=result.content_type.type_name,
                content_name=get_content_name(result),
                workspace_id=result.workspace_id,
                workspace_name=result.workspace.display_name,
                source_content_id=result.source_content_id,
                codebase_id=result.codebase_id,
                codebase_name=result.codebase.codebase_name
                if result.codebase
                else None,
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
            )
            for result in sources
        ]
        return ContentSourceResponse(results=source_results)

    def get_content_by_id(
        self, content_id: UUID, organization_id: str
    ) -> DerivedContent:
        logger.info(f"Fetching content by ID {content_id}")

        content: DerivedContent | None = self.content_repository.get(content_id)

        if not content:
            logger.error(f"Content {content_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        checks = [
            lambda session: self.content_repository.is_authorized(
                id=content_id,
                relationship_chain=["workspace"],
                field_name="organization_id",
                field_value=organization_id,
            )
        ]

        perform_authorization_checks(self.session, checks)

        return content

    def get_content_root_by_id(
        self, content_id: UUID, user_org_id: str
    ) -> DerivedContent:
        """
        Get the root codebase content record for a given content ID. this is need by the frontend to appropriately
        add document sources.
        """
        logger.info(f"Fetching content by ID {content_id}")
        content = self.content_repository.get(content_id)
        if not content:
            logger.error(f"Content {content_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        checks = [
            lambda session: is_authorized(
                session, user_org_id, content.workspace_id, content.codebase_id
            )
        ]

        perform_authorization_checks(self.session, checks)

        parent = self.session.exec(
            select(DerivedContent)
            .join(DerivedContentType)
            .where(DerivedContent.codebase_id == content.codebase_id)
            .where(DerivedContentType.type_name == "codebase")
        ).first()

        return parent

    def edit_content(
        self, organization_id: str, content_id: UUID, new_content: dict
    ) -> DerivedContent:
        logger.info(f"Editing content {content_id} for organization {organization_id}")

        content = self.content_repository.get_by_conditions(
            [
                Workspace.organization_id == organization_id,
                DerivedContent.id == content_id,
            ],
            [Workspace],
        )

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        if (
            content.content_type.type_name
            != DerivedContentTypeNames.APPLICATION_NOTE.value
            and content.content_type.type_name != DerivedContentTypeNames.TEMPLATE.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type"
            )

        content = self.content_repository.update(content, DerivedContent(**new_content))

        logger.info(
            f"Content {content_id} successfully edited for organization {organization_id}"
        )

        return content

    def get_content_download_url(
        self, content_id: UUID, organization_id: str
    ) -> DownloadContentResponse:
        """
        Get a presigned URL for downloading this content from S3
        """
        logger.info(f"Fetching content by ID {content_id}")

        checks = [
            lambda session: self.content_repository.is_authorized(
                id=content_id,
                relationship_chain=["workspace"],
                field_name="organization_id",
                field_value=organization_id,
            )
        ]

        perform_authorization_checks(self.session, checks)

        content: DerivedContent | None = self.content_repository.get_by_conditions(
            [
                Workspace.organization_id == organization_id,
                DerivedContent.id == content_id,
                DerivedContentType.type_name
                == DerivedContentTypeNames.SUPPLEMENTAL_DOCUMENT.value,
            ],
            [Workspace, DerivedContentType],
        )

        if not content:
            logger.error(f"Content {content_id} not found or not downloadable")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or not downloadable",
            )

        # TODO: This is the new way. How do we fetch the old way? head_object then fall back to different path?
        download_key = f"documents/{content.relative_path}"
        if aws_s3.head_org_object(organization_id, download_key):
            return DownloadContentResponse(
                download_url=aws_s3.generate_org_get_presigned_url(
                    organization_id, download_key
                ),
                content_name=content.content_name,
            )
        logger.info(
            "Falling back to legacy way of fetching download URL w/ codebase ID"
        )
        download_key = f"{content.codebase_id}/documents/{content.relative_path}"
        if aws_s3.head_org_object(organization_id, download_key):
            return DownloadContentResponse(
                download_url=aws_s3.generate_org_get_presigned_url(
                    organization_id, download_key
                ),
                content_name=content.content_name,
            )
        logger.error("Content not found or not downloadable")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or not downloadable",
        )
