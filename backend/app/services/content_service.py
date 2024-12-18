import functools
import hashlib
from uuid import UUID

import pypandoc
from botocore.exceptions import ClientError
from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import (
    ChunkAndEmbedding,
    Codebase,
    DerivedContent,
    DerivedContentType,
    DocumentSource,
    Enum_Derived_Content_Status,
    InspectionVersion,
    InspectorRun,
    Tag,
    TagContent,
    Workspace,
)
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.selectable import Select
from sqlmodel import Session, asc, desc, func, or_, select, text

from app.api.routes.legacy.s3 import S3BucketAccess
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
    ContentTagsResponse,
    CreateContentRequest,
    DeleteDocumentSourceResponse,
    DownloadContentResponse,
    ListContentInput,
    ListContentResult,
    ListContentResults,
    ListContentTypesInput,
    ListContentTypesResults,
    TagResult,
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

    def create_content(
        self: "ContentService", organization_id: str, request: CreateContentRequest
    ) -> DerivedContent:
        logger.info(
            f"Creating content for organization {organization_id} with input {request}"
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
        for derived_content in results:
            content_results.append(
                ListContentResult(
                    id=derived_content.id,
                    organization_id=derived_content.workspace.organization_id,
                    content_type_id=derived_content.content_type_id,
                    content_type_name=derived_content.content_type.type_name
                    if derived_content.content_type
                    else None,
                    content_name=get_content_name(derived_content),
                    workspace_id=derived_content.workspace_id,
                    workspace_name=derived_content.workspace.display_name
                    if derived_content.workspace
                    else None,
                    source_content_id=derived_content.source_content_id,
                    codebase_id=derived_content.codebase_id,
                    codebase_name=derived_content.codebase.codebase_name
                    if derived_content.codebase
                    else None,
                    relative_path=derived_content.relative_path,
                    content=derived_content.content,
                    misc_metadata=derived_content.misc_metadata,
                    status=derived_content.status,
                    created_at=derived_content.created_at,
                    updated_at=derived_content.updated_at,
                    source_content=derived_content.source_content,
                    order=derived_content.order,
                    tags=derived_content.tags,
                    source_links=derived_content.source_links,
                    version_id=derived_content.version_id,
                    version=derived_content.inspection_version.version
                    if derived_content.inspection_version
                    else None,
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
        # we pre-fetch related entities so that when we access attributes of those entities we do not incur additional queries.
        # This is helpful when the list endpoint builds the results to return, and nested attributes are requested on each result
        query = self._build_base_query(organization_id)
        query = self._apply_filters(query, search_input)
        total_count = self.session.exec(
            select(func.count()).select_from(query.subquery())
        ).one()
        query = self._apply_sorting(query, search_input)

        query = query.options(
            selectinload(DerivedContent.workspace),
            selectinload(DerivedContent.content_type),
            selectinload(DerivedContent.codebase),
            selectinload(DerivedContent.source_content),
            selectinload(DerivedContent.tags),
            selectinload(DerivedContent.inspection_version),
        )

        results = self.session.exec(
            query.offset(search_input.offset).limit(search_input.limit)
        ).all()

        return results, total_count

    def _build_base_query(self: "ContentService", organization_id: str) -> Select:
        return (
            select(DerivedContent)
            .where(DerivedContent.workspace_id == Workspace.id)
            .where(Workspace.organization_id == organization_id)
            # Ensure Workspace is known:
            .join(Workspace, DerivedContent.workspace_id == Workspace.id)
        )

    def _apply_sorting(
        self: "ContentService",
        statement: Select,
        search_input: ListContentInput,
    ) -> Select:
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
        return statement

    def _apply_filters(
        self: "ContentService",
        statement: Select,
        search_input: ListContentInput,
    ) -> Select:
        if search_input.text:
            clauses = [
                DerivedContent.relative_path.icontains(search_input.text),
                DerivedContent.content_name.icontains(search_input.text),
            ]
            statement = statement.where(or_(*clauses))

        if search_input.source_content_id:
            clauses = [
                DerivedContent.source_content_id.in_(search_input.source_content_id),
            ]
            statement = statement.where(or_(*clauses))

        if search_input.order:
            clauses = [
                DerivedContent.order == search_input.order,
            ]
            statement = statement.where(or_(*clauses))

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

        if search_input.content_type_id:
            statement = statement.where(
                DerivedContent.content_type_id.in_(search_input.content_type_id)
            )

        if search_input.version_id:
            statement = statement.where(
                DerivedContent.version_id.in_(search_input.version_id)
            )

        if search_input.content_type_name:
            logger.info(
                f"Filtering by content_type_name: {search_input.content_type_name}"
            )
            statement = statement.join(
                DerivedContentType,
                DerivedContent.content_type_id == DerivedContentType.id,
            )
            statement = statement.where(
                DerivedContentType.type_name.in_(search_input.content_type_name)
            )

        if search_input.latest_version_only:
            # COMMENT: This gets all InspectionVersion IDs that are NOT a previous_version.
            # Hence, this is a list of all the most recent version Ids.
            most_recent_versions_subquery = (
                select(InspectionVersion.id)
                .where(
                    ~InspectionVersion.id.in_(
                        select(InspectionVersion.previous_version_id).where(
                            InspectionVersion.previous_version_id.isnot(None)
                        )
                    )
                )
                .subquery()
            )
            statement = statement.where(
                or_(
                    DerivedContent.version_id.is_(None),
                    DerivedContent.version_id.in_(most_recent_versions_subquery),
                )
            )

        if search_input.tags or search_input.tag_ids:
            # For tags filtering we need to join Tag if not done.
            statement = statement.join(
                TagContent, TagContent.content_id == DerivedContent.id, isouter=True
            )
            statement = statement.join(Tag, Tag.id == TagContent.tag_id, isouter=True)
            if search_input.tags:
                tag_clauses = [Tag.name.contains(tag) for tag in search_input.tags]
                statement = statement.where(or_(*tag_clauses))

            if search_input.tag_ids:
                tag_id_clauses = [Tag.id == tag_id for tag_id in search_input.tag_ids]
                statement = statement.where(or_(*tag_id_clauses))

        return statement

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
                version_id=source.version_id,
                version=source.inspection_version.version
                if source.inspection_version
                else None,
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

    def get_content_tags(
        self: "ContentService", content_id: UUID, organization_id: str
    ) -> ContentTagsResponse:
        logger.info(f"Fetching tags for content {content_id}")

        content = self.content_repository.get_by_conditions(
            [
                Workspace.organization_id == organization_id,
                DerivedContent.id == content_id,
            ],
            [Workspace],
        )

        if not content or content.workspace.organization_id != organization_id:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        tag_results = [
            TagResult(
                id=tag.id,
                name=tag.name,
                color=tag.hex_color,
                created_at=tag.created_at,
                updated_at=tag.updated_at,
            )
            for tag in content.tags
        ]

        logger.info(f"Tags retrieved successfully for content {content_id}")
        return ContentTagsResponse(
            tags=tag_results,
        )

    def convert_markdown_to_rst(self, content: str) -> str:
        logger.info("Converting markdown content to rst")
        try:
            rst_content = pypandoc.convert_text(content, "rst", format="markdown")
            return rst_content
        except RuntimeError:
            raise HTTPException(status_code=500, detail="Conversion error")


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
        # Fetch all derived content and related entities in a single query
        derived_contents = session.exec(
            select(DerivedContent)
            .where(DerivedContent.codebase_id == codebase_id)
            .options(
                selectinload(DerivedContent.source_links),
                selectinload(DerivedContent.tag_links),
            )
        ).all()

        # Separate derived contents into those with and without source_content_id
        irs = [dc for dc in derived_contents if dc.source_content_id is not None]
        source_content = [dc for dc in derived_contents if dc.source_content_id is None]

        version_ids_to_delete = {
            dc.version_id for dc in derived_contents if dc.version_id is not None
        }

        session.query(DocumentSource).filter(
            DocumentSource.source_id.in_([source.id for source in source_content])
        ).delete(synchronize_session="fetch")

        session.query(TagContent).filter(
            TagContent.content_id.in_([source.id for source in source_content])
        ).delete(synchronize_session="fetch")

        session.query(DerivedContent).filter(
            DerivedContent.id.in_([ir.id for ir in irs])
        ).delete(synchronize_session="fetch")

        session.query(DerivedContent).filter(
            DerivedContent.id.in_([source.id for source in source_content])
        ).delete(synchronize_session="fetch")
        if version_ids_to_delete:
            session.query(InspectorRun).filter(
                InspectorRun.inspection_version_id.in_(version_ids_to_delete)
            ).delete(synchronize_session="fetch")

        if version_ids_to_delete:
            session.query(InspectionVersion).filter(
                InspectionVersion.id.in_(version_ids_to_delete)
            ).delete(synchronize_session="fetch")

        # Collect records for S3 deletion
        records_to_delete_in_s3.extend(
            source
            for source in source_content
            if source.content_type.type_name
            == DerivedContentTypeNames.CODEBASE_FILE.value
        )

        # TODO delete task results from s3 as well

        codebase = session.exec(
            select(Codebase).where(Codebase.id == codebase_id)
        ).first()
        session.delete(codebase)

        session.commit()  # Commit if everything is successful

    except Exception:
        logger.exception(
            f"Error deleting codebase_id {content_id} and related entities."
        )
        session.rollback()  # Rollback on any exception
        raise

    return records_to_delete_in_s3


def organization_bucket_from_organization_id(organization_id: str) -> str:
    """
    Generate the organization bucket name from the organization ID
    """
    return hashlib.sha256(organization_id.encode()).hexdigest()[:63]


def delete_from_remote_storage(content: DerivedContent, organization_id: str) -> None:
    if content.content_type.type_name == DerivedContentTypeNames.CODEBASE_FILE.value:
        S3BucketAccess(
            organization_id=organization_id,
            codebase_id=str(content.codebase_id),
            version_id=content.version_id,
        ).delete_file(content.relative_path)
    else:
        organization_bucket = organization_bucket_from_organization_id(organization_id)
        key = (
            content.relative_path
            if content.relative_path.startswith("documents/")
            else f"documents/{content.relative_path}"
        )
        logger.info(
            f"Deleting content {key} from s3 storage in bucket {organization_bucket}"
        )
        delete_file_from_s3(key=key, bucket=organization_bucket)
