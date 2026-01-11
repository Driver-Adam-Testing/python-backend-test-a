import logging
from uuid import UUID

import pypandoc
from botocore.exceptions import ClientError
from database.models import (
    DerivedContent,
    Enum_Derived_Content_Status,
    Node,
    PrimaryAsset,
    PrimaryAssetTag,
    Tag,
    Version,
    VersionNode,
)
from fastapi import HTTPException, status
from sqlalchemy.sql.selectable import Select
from sqlmodel import Session, asc, desc, func, or_, select, text

from app.repositories.base_repository import BaseRepository
from app.schemas.content_schema import (
    DownloadContentResponse,
    ListContentInput,
    ListContentResult,
    ListContentResults,
)
from app.utils.aws_s3 import (
    generate_org_get_presigned_url,
    head_org_object,
)

# TODO adapt self.content_repository.get to also accept org_id as an argument to avoid the need to check the org_id in the service methods
logger = logging.getLogger(__name__)


class ContentService:
    def __init__(self: "ContentService", session: Session) -> None:
        self.session = session
        self.content_repository = BaseRepository(session, DerivedContent)

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
                    organization_id=organization_id,
                    content_name=derived_content.content_kind,
                    codebase_name=None,
                    relative_path=None,  # derived contents can be associated with multiple relative paths
                    content=derived_content.content,
                    misc_metadata=derived_content.misc_metadata,
                    status=None,  # derived contents can be associated with multiple primary assets each with a different status
                    created_at=derived_content.created_at,
                    updated_at=derived_content.updated_at,
                    source_content=None,
                    order=derived_content.order,
                    tags=[],
                    source_links=None,
                    version_id=None,
                    version=None,
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
        query = query.distinct()
        total_count = self.session.exec(
            select(func.count()).select_from(query.subquery())
        ).one()
        query = self._apply_sorting(query, search_input)

        results = self.session.exec(
            query.offset(search_input.offset).limit(search_input.limit)
        ).all()

        return results, total_count

    def _build_base_query(self: "ContentService", organization_id: str) -> Select:
        """
        Constructs the base SQL query for retrieving content-related data from the database.
        The resulting query is used as a foundational query for further filtering and
        processing in other parts of the ContentService.
        """
        return (
            select(DerivedContent)
            .join(Node, DerivedContent.node_id == Node.id)
            .join(VersionNode, VersionNode.node_id == Node.id)
            .join(Version, VersionNode.version_id == Version.id)
            .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
            .where(PrimaryAsset.organization_id == organization_id)
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
                VersionNode.relative_path.icontains(search_input.text),
                PrimaryAsset.display_name.icontains(search_input.text),
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
            statement = statement.where(Version.status == search_input.status)

        if search_input.version_id:
            statement = statement.where(Version.id == search_input.version_id)

        if search_input.content_type_name:
            logger.info(
                f"Filtering by content_type_name: {search_input.content_type_name}"
            )
            statement = statement.where(
                DerivedContent.content_kind.in_(search_input.content_type_name)
            )

        if (search_input.tags and any(search_input.tags)) or (
            search_input.tag_ids and any(search_input.tag_ids)
        ):
            # For tags filtering we need to join Tag if not done.
            statement = statement.join(PrimaryAssetTag)
            statement = statement.join(Tag)
            if search_input.tags and any(search_input.tags):
                tag_clauses = [
                    Tag.name.contains(tag) for tag in search_input.tags if tag
                ]
                statement = statement.where(or_(*tag_clauses))

            if search_input.tag_ids and any(search_input.tag_ids):
                tag_id_clauses = [
                    Tag.id == tag_id for tag_id in search_input.tag_ids if tag_id
                ]
                statement = statement.where(or_(*tag_id_clauses))

        return statement

    def get_content_download_url(
        self, version_node_id: UUID, organization_id: str
    ) -> DownloadContentResponse:
        """
        Get a presigned URL for downloading this content from S3
        """
        logger.info(f"Fetching content by ID {version_node_id}")

        query = (
            select(VersionNode)
            .join(Version, VersionNode.version_id == Version.id)
            .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
            .where(VersionNode.id == version_node_id)
            .where(PrimaryAsset.organization_id == organization_id)
        )
        version_node = self.session.exec(query).one_or_none()

        if not version_node:
            logger.error(f"Content {version_node_id} not found or not downloadable")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or not downloadable",
            )
        download_key = f"{version_node.version.primary_asset_id}/{version_node.version_id}/{version_node.relative_path}"
        logger.info(f"Trying download_key={download_key}")
        try:
            if head_org_object(organization_id, download_key):
                # TODO: use the shared library for get_presigned_url
                return DownloadContentResponse(
                    download_url=generate_org_get_presigned_url(
                        organization_id, download_key
                    ),
                    content_name=version_node.version.primary_asset.display_name,
                    status=version_node.version.status,
                    primary_asset_id=version_node.version.primary_asset.id,
                )
        except ClientError:
            logger.exception("Content not found or not downloadable")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or not downloadable",
            )

    def convert_markdown_to_rst(self, content: str) -> str:
        logger.info("Converting markdown content to rst")
        try:
            rst_content = pypandoc.convert_text(content, "rst", format="markdown")
            return rst_content
        except RuntimeError:
            raise HTTPException(status_code=500, detail="Conversion error")
