import functools
import hashlib
import json
from datetime import datetime
from uuid import UUID

from botocore.exceptions import ClientError
from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import (
    ChunkAndEmbedding,
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
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.sql.selectable import Select
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
from app.utils.aws_s3 import (
    delete_file_from_s3,
    generate_org_get_presigned_url,
    head_org_object,
)

# TODO adapt self.content_repository.get to also accept org_id as an argument to avoid the need to check the org_id in the service methods


class ContentService:
    def __init__(self: "ContentService", session: Session) -> None:
        self.session = session
        self.content_repository = BaseRepository(session, DerivedContent)
        self.workspace_repository = WorkspaceRepository(session)
        self.derived_content_type_repository = DerivedContentTypeRepository(session)
        self.document_source_repository = BaseRepository(session, DocumentSource)
        self.tag_content_repository = BaseRepository(session, TagContent)

    def associate_sources_with_content(
        self: "ContentService",
        organization_id: str,
        content_id: UUID,
        content_source_associations: list[ContentSourceAssociationItem],
    ) -> BatchContentSourceAssociationResponse:
        logger.info(
            f"Associating {len(content_source_associations)} sources with content {content_id} for organization {organization_id}"
        )

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

    def disassociate_document_source(
        self: "ContentService",
        organization_id: str,
        content_id: UUID,
        source_content_id: UUID,
    ) -> DeleteDocumentSourceResponse:
        logger.info(
            f"Disassociating source {source_content_id} from content {content_id} for organization {organization_id}"
        )
        content = self.content_repository.get(content_id)

        if not content or content.workspace.organization_id != organization_id:
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
        self: "ContentService",
        organization_id: str,
        workspace_id: UUID,
        codebase_id: UUID,
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
        self: "ContentService", organization_id: str, request: CreateContentRequest
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

    def get_list_content(
        self: "ContentService", organization_id: str, search_input: ListContentInput
    ) -> ListContentResults:
        logger.info(
            f"Getting list of content for organization {organization_id} with input {search_input}"
        )
        try:
            results, total_count = self._get_list_content(organization_id, search_input)
        except ValueError:
            logger.exception(
                f"Error getting list of content for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request"
            )

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
        self: "ContentService", organization_id: str, search_input: ListContentInput
    ) -> tuple[list[DerivedContent], int]:
        statement = self._build_base_query(organization_id)
        count_statement = self._build_base_count_query(organization_id, search_input)

        statement, count_statement = self._apply_filters(
            statement, count_statement, search_input
        )
        statement, count_statement = self._apply_sorting(
            statement, count_statement, search_input
        )

        total_count = self.session.exec(count_statement).one()
        results = self.session.exec(
            statement.offset(search_input.offset).limit(search_input.limit)
        ).all()

        return results, total_count

    def _build_base_query(self: "ContentService", organization_id: str) -> Select:
        return (
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

    def _build_base_count_query(
        self: "ContentService", organization_id: str, search_input: ListContentInput
    ) -> Select:
        if search_input.tag_ids:
            """
            When tag_ids are provided, a join with Tag and TagContent is required
            to accurately count the content associated with the specified tag_ids.
            """
            return (
                select(func.count(DerivedContent.id))
                .join(DerivedContentType)
                .join(Workspace)
                .join(TagContent, isouter=True)
                .join(Tag, isouter=True)
                .where(organization_id == Workspace.organization_id)
            )
        else:
            """
             If no tag_ids are provided, skip the join with TagContent and Tag.
             Performing the join without tag_ids affects the count due to the nature of the LEFT OUTER JOIN.
            Consult Eric and Jesse for further details on the underlying issue.
            """
            return (
                select(func.count(DerivedContent.id))
                .join(DerivedContentType)
                .join(Workspace)
                .where(organization_id == Workspace.organization_id)
            )

    def _apply_sorting(
        self: "ContentService",
        statement: Select,
        count_statement: Select,
        search_input: ListContentInput,
    ) -> tuple[Select, Select]:
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
        return statement, count_statement

    def _apply_filters(
        self: "ContentService",
        statement: Select,
        count_statement: Select,
        search_input: ListContentInput,
    ) -> tuple[Select, Select]:
        if search_input.text:
            clauses = [
                DerivedContent.relative_path.icontains(search_input.text),
                DerivedContent.content_name.icontains(search_input.text),
            ]
            statement = statement.where(or_(*clauses))
            count_statement = count_statement.where(or_(*clauses))

        if search_input.source_content_id:
            clauses = [
                DerivedContent.source_content_id.in_(search_input.source_content_id),
            ]
            statement = statement.where(or_(*clauses))
            count_statement = count_statement.where(or_(*clauses))

        if search_input.order:
            clauses = [
                DerivedContent.order == search_input.order,
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
            tag_clauses = [Tag.name.contains(tag) for tag in search_input.tags]
            statement = statement.where(or_(*tag_clauses))
            count_statement = count_statement.where(or_(*tag_clauses))

        if search_input.tag_ids:
            tag_id_clauses = [Tag.id == tag_id for tag_id in search_input.tag_ids]
            tag_contents_clauses = [
                TagContent.tag_id == tag_id for tag_id in search_input.tag_ids
            ]
            statement = statement.where(or_(*tag_id_clauses))
            # tag_contents_clauses is used in the count statement to accurately count the content associated with the specified tag_ids
            count_statement = count_statement.where(or_(*tag_contents_clauses))

        return statement, count_statement

    def get_list_content_types(
        self: "ContentService", lct_inputs: ListContentTypesInput
    ) -> ListContentTypesResults:
        logger.info(f"Getting list of content types with input {lct_inputs}")
        try:
            results = self.derived_content_type_repository.get_all(
                lct_inputs.limit,
                lct_inputs.offset,
                lct_inputs.sort_by,
                lct_inputs.sort_direction,
            )
        except ValueError:
            logger.exception("Error getting list of content types")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request"
            )

        logger.info("List of content types retrieved successfully")
        return ListContentTypesResults(results=results)

    def get_content_sources(
        self: "ContentService", content_id: UUID, organization_id: str
    ) -> ContentSourceResponse:
        logger.info(f"Fetching content sources for content {content_id}")

        content = self.content_repository.get(content_id)
        if not content or content.workspace.organization_id != organization_id:
            logger.error(f"Content {content_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        sources = [link.source for link in content.source_links]

        # We need caching, so bypassing content service stuff.
        @functools.cache
        def get_codebase(codebase_id: UUID) -> Codebase | None:
            return self.session.exec(
                select(Codebase).where(Codebase.id == codebase_id)
            ).first()

        codebase_file_id = self.derived_content_type_repository.get_by_type_name(
            "codebase-file"
        ).id
        codebase_directory_id = self.derived_content_type_repository.get_by_type_name(
            "codebase-directory"
        ).id

        # Apply the codebase status to the file and folder DC statuses. This is required for the frontend
        # to know if a source can be used for search/agents.
        for source in sources:
            if source.codebase_id and source.content_type_id in {
                codebase_file_id,
                codebase_directory_id,
            }:
                codebase = get_codebase(source.codebase_id)
                derived_content_status: Enum_Derived_Content_Status = (
                    codebase.status.into_dc_status()
                )
                source.status = derived_content_status

        # If the source is associated with a codebase, get the codebase status and propagate to children

        logger.info(f"Content sources resolved for content {content_id}")
        source_results = [
            ListContentResult(
                id=source.id,
                organization_id=source.workspace.organization_id,
                content_type_id=source.content_type_id,
                content_type_name=source.content_type.type_name,
                content_name=get_content_name(source),
                workspace_id=source.workspace_id,
                workspace_name=source.workspace.display_name,
                source_content_id=source.source_content_id,
                codebase_id=source.codebase_id,
                codebase_name=source.codebase.codebase_name
                if source.codebase
                else None,
                relative_path=source.relative_path,
                content=source.content,
                misc_metadata=source.misc_metadata,
                status=source.status,
                created_at=source.created_at,
                updated_at=source.updated_at,
                source_content=source.source_content,
                order=source.order,
                tags=source.tags,
                source_links=source.source_links,
            )
            for source in sources
        ]
        return ContentSourceResponse(results=source_results)

    def get_content_by_id(
        self: "ContentService", content_id: UUID, organization_id: str
    ) -> DerivedContent:
        logger.info(f"Fetching content by ID {content_id}")

        content: DerivedContent | None = self.content_repository.get(content_id)

        if not content or content.workspace.organization_id != organization_id:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        return content

    def get_content_root_by_id(
        self: "ContentService", content_id: UUID, user_org_id: str
    ) -> DerivedContent:
        """
        Get the root codebase content record for a given content ID. this is need by the frontend to appropriately
        add document sources.
        """
        logger.info(f"Fetching content by ID {content_id}")
        content = self.content_repository.get(content_id)
        if not content or content.workspace.organization_id != user_org_id:
            logger.error(f"Content {content_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        parent = self.session.exec(
            select(DerivedContent)
            .join(DerivedContentType)
            .where(DerivedContent.codebase_id == content.codebase_id)
            .where(DerivedContentType.type_name == "codebase")
        ).first()

        return parent

    def edit_content(
        self: "ContentService",
        organization_id: str,
        content_id: UUID,
        new_content: dict,
    ) -> DerivedContent:
        logger.info(f"Editing content {content_id} for organization {organization_id}")

        content = self.content_repository.get_by_conditions(
            [
                Workspace.organization_id == organization_id,
                DerivedContent.id == content_id,
            ],
            [Workspace],
        )

        if not content or content.workspace.organization_id != organization_id:
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

        content: DerivedContent | None = self.content_repository.get_by_conditions(
            [
                Workspace.organization_id == organization_id,
                DerivedContent.id == content_id,
                DerivedContentType.type_name
                == DerivedContentTypeNames.SUPPLEMENTAL_DOCUMENT.value,
            ],
            [Workspace, DerivedContentType],
        )

        if not content or content.workspace.organization_id != organization_id:
            logger.error(f"Content {content_id} not found or not downloadable")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or not downloadable",
            )

        download_key = (
            f"documents/{content.relative_path}"
            if content.codebase_id is None
            else f"{content.codebase_id}/{content.relative_path}"
        )
        logger.info(f"Trying download_key={download_key}")
        try:
            if head_org_object(organization_id, download_key):
                return DownloadContentResponse(
                    download_url=generate_org_get_presigned_url(
                        organization_id, download_key
                    ),
                    content_name=content.content_name or "",
                )
        except ClientError:
            logger.exception("Content not found or not downloadable")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or not downloadable",
            )

    def delete_content(self, organization_id: str, content_id: UUID) -> None:
        logger.info(f"Deleting content {content_id} for organization {organization_id}")

        # Check if the content exists and is associated with the organization
        content = self.content_repository.get_by_conditions(
            [
                Workspace.organization_id == organization_id,
                DerivedContent.id == content_id,
            ],
            [Workspace],
        )

        if not content or content.workspace.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        valid_content_types = {
            DerivedContentTypeNames.APPLICATION_NOTE.value,
            DerivedContentTypeNames.TEMPLATE.value,
            DerivedContentTypeNames.SUPPLEMENTAL_DOCUMENT.value,
            DerivedContentTypeNames.CODEBASE.value,
        }

        if content.content_type.type_name not in valid_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type"
            )

        if content.content_type.type_name == DerivedContentTypeNames.CODEBASE.value:
            records_to_delete_in_s3 = delete_codebase_and_related_entities(
                self.session, self, content_id
            )
            # delete remote content
            for record in records_to_delete_in_s3:
                logger.info(
                    f"Deleting content {record.relative_path} from remote storage"
                )
                try:
                    delete_from_remote_storage(record, organization_id)
                except Exception:
                    """
                    if we get here the bucket or content might not exist.
                    This was added because automated testing was failing since the content is made up and does not exist in the bucket.
                    See Eric for more information.
                    """
                    logger.exception(
                        f"Error deleting content {record.id} from remote storage"
                    )
        else:
            try:
                delete_document_and_related_entities(self.session, content)
                logger.info(
                    f"Content {content_id} successfully deleted for organization {organization_id}"
                )
            except IntegrityError:
                logger.exception(f"Error deleting content {content_id}")
                raise HTTPException(status_code=400, detail="Error deleting content")

            if content.content_type.type_name == "supplemental-document":
                # delete remote content
                delete_from_remote_storage(content, organization_id)


def delete_document_and_related_entities(
    session: Session, content: DerivedContent
) -> None:
    try:
        # Delete related DocumentSource entities
        document_sources = session.exec(
            select(DocumentSource).where(
                or_(
                    # fetch all document sources associated with the content. e.g. content is an app note
                    DocumentSource.document_id == content.id,
                    # fetch all document sources that are sources for the content.
                    # e.g. content is a pdf and is a source for a note.
                    DocumentSource.source_id == content.id,
                )
            )
        ).all()
        # Deleting Many-to-Many relationship requires fetching the related entities and deleting them
        for document_source in document_sources:
            session.delete(document_source)

        # Delete related TagContent entities
        tag_contents = session.exec(
            select(TagContent).where(TagContent.content_id == content.id)
        ).all()

        for tag_content in tag_contents:
            session.delete(tag_content)

        # Delete related ChunkAndEmbed entities
        chunk_and_embeddings = session.exec(
            select(ChunkAndEmbedding).where(ChunkAndEmbedding.content_id == content.id)
        ).all()

        for chunk_and_embedding in chunk_and_embeddings:
            session.delete(chunk_and_embedding)

        # Delete all the derived contents associated with the document
        for derived_content in content.derived_contents:
            session.delete(derived_content)

        session.delete(content)
    # except IntegrityError:
    except:
        logger.exception(f"Error deleting content {content.id}")
        session.rollback()
        raise
    else:
        # if not session.in_transaction():
        session.commit()


def delete_document_sources_uncommited(session: Session, content_id: UUID) -> None:
    # Delete related DocumentSource entities
    document_sources = session.exec(
        select(DocumentSource).where(
            or_(
                # fetch all document sources associated with the content. e.g. content is an app note
                DocumentSource.document_id == content_id,
                # fetch all document sources that are sources for the content.
                # e.g. content is a pdf and is a source for a note.
                DocumentSource.source_id == content_id,
            )
        )
    ).all()
    # Deleting Many-to-Many relationship requires fetching the related entities and deleting them
    for document_source in document_sources:
        session.delete(document_source)


def delete_codebase_and_related_entities(
    session: Session, service: ContentService, content_id: UUID
) -> list[DerivedContent]:
    records_to_delete_in_s3 = []
    codebase_record = service.content_repository.get(content_id)
    if not codebase_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Codebase not found"
        )

    codebase_id = codebase_record.codebase_id

    try:
        # get all derived content associated with the codebase
        derived_contents = session.exec(
            select(DerivedContent).where(DerivedContent.codebase_id == codebase_id)
        ).all()

        # select derived_contents where source_content_id is not null
        irs = [
            derived_content
            for derived_content in derived_contents
            if derived_content.source_content_id is not None
        ]

        for ir in irs:
            session.delete(ir)

        # Delete related TagContent entities for the codebase
        tag_contents = session.exec(
            select(TagContent).where(TagContent.content_id == content_id)
        ).all()

        for tag_content in tag_contents:
            session.delete(tag_content)

        # delete the derived_contents where source_content_id is null and codebase_id = codebase_id
        source_content = [
            derived_content
            for derived_content in derived_contents
            if derived_content.source_content_id is None
        ]

        for source in source_content:
            session.delete(source)
            if (
                source.content_type.type_name
                == DerivedContentTypeNames.CODEBASE_FILE.value
            ):
                records_to_delete_in_s3.append(source)

        # delete the codebase record
        codebase = session.exec(
            select(Codebase).where(Codebase.id == codebase_id)
        ).first()

        session.delete(codebase)
    except:
        # except Exception as e:
        logger.exception(
            f"Error deleting codebase_id {content_id} and related entities"
        )
        session.rollback()
        raise
    else:
        session.commit()
        return records_to_delete_in_s3


def organization_bucket_from_organization_id(organization_id: str) -> str:
    """
    Generate the organization bucket name from the organization ID
    """
    return hashlib.sha256(organization_id.encode()).hexdigest()[:63]


def delete_from_remote_storage(content: DerivedContent, organization_id: str) -> None:
    organization_bucket = organization_bucket_from_organization_id(organization_id)
    if content.content_type.type_name == DerivedContentTypeNames.CODEBASE_FILE.value:
        key = f"{content.codebase_id}/source/{content.relative_path}"
    else:
        key = (
            content.relative_path
            if content.relative_path.startswith("documents/")
            else f"documents/{content.relative_path}"
        )
    logger.info(
        f"Deleting content {key} from s3 storage in bucket {organization_bucket}"
    )
    delete_file_from_s3(key=key, bucket=organization_bucket)
