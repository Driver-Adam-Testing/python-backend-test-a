import hashlib
from uuid import UUID

import pypandoc
from botocore.exceptions import ClientError
from database.models_v1 import (
    DerivedContent,
    DocumentSource,
    Enum_Derived_Content_Status,
)
from database.models_v2 import Node, PrimaryAsset, PrimaryAssetTag, Tag, Version
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.selectable import Select
from sqlmodel import Session, asc, desc, func, or_, select, text

from app.core.logger import logger
from app.repositories.base_repository import BaseRepository
from app.schemas.content_schema import (
    ContentTagsResponse,
    DownloadContentResponse,
    ListContentInput,
    ListContentResult,
    ListContentResults,
    TagResult,
)
from app.utils.aws_s3 import (
    generate_org_get_presigned_url,
    head_org_object,
)

# TODO adapt self.content_repository.get to also accept org_id as an argument to avoid the need to check the org_id in the service methods


class ContentService:
    def __init__(self: "ContentService", session: Session) -> None:
        self.session = session
        self.content_repository = BaseRepository(session, DerivedContent)
        self.document_source_repository = BaseRepository(session, DocumentSource)
        self.node_repository = BaseRepository(session, Node)

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
                    relative_path=derived_content.relative_path,
                    content=derived_content.content,
                    misc_metadata=derived_content.misc_metadata,
                    status=derived_content.node.version.status,
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
        total_count = self.session.exec(
            select(func.count()).select_from(query.subquery())
        ).one()
        query = self._apply_sorting(query, search_input)

        query = query.options(
            selectinload(DerivedContent.node),
        )

        results = self.session.exec(
            query.offset(search_input.offset).limit(search_input.limit)
        ).all()

        return results, total_count

    def _build_base_query(self: "ContentService", organization_id: str) -> Select:
        """
        Constructs the base SQL query for retrieving content-related data from the database.
        It selects data from four tables: NodeRow, DerivedContent, VersionRow, and PrimaryAssetRow.
        The function performs the following operations:
        1. Selects columns from NodeRow, DerivedContent, VersionRow, and PrimaryAssetRow.
        2. Joins the DerivedContent table with NodeRow using a left outer join on the node_id.
           This ensures that all NodeRow entries are included, even if they don't have a
           corresponding entry in DerivedContent.
        3. Joins the VersionRow table with NodeRow on the version_id, ensuring that each
           node is associated with its version.
        4. Joins the PrimaryAssetRow table with VersionRow on the primary_asset_id, linking
           each version to its primary asset.
        5. Filters the results to include only those entries where the organization_id in
           PrimaryAssetRow matches the provided organization_id parameter.

        The resulting query is used as a foundational query for further filtering and
        processing in other parts of the ContentService.
        """
        return (
            select(DerivedContent)
            .join(Node)
            .join(Version)
            .join(PrimaryAsset)
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
                Node.relative_path.icontains(search_input.text),
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

    def get_content_download_url(
        self, node_id: UUID, organization_id: str
    ) -> DownloadContentResponse:
        """
        Get a presigned URL for downloading this content from S3
        """
        logger.info(f"Fetching content by ID {node_id}")

        node: Node | None = self.node_repository.get_by_conditions(
            [
                Node.id == node_id,
                PrimaryAsset.organization_id == organization_id,
            ],
            [Version, PrimaryAsset],
        )

        if not node or node.version.primary_asset.organization_id != organization_id:
            logger.error(f"Content {node_id} not found or not downloadable")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or not downloadable",
            )

        download_key = (
            f"{node.version.primary_asset_id}/{node.version_id}/{node.relative_path}"
        )
        logger.info(f"Trying download_key={download_key}")
        try:
            if head_org_object(organization_id, download_key):
                # TODO: use the shared library for get_presigned_url
                return DownloadContentResponse(
                    download_url=generate_org_get_presigned_url(
                        organization_id, download_key
                    ),
                    content_name=node.version.primary_asset.display_name,
                    status=node.version.status,
                )
        except ClientError:
            logger.exception("Content not found or not downloadable")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or not downloadable",
            )

    def get_content_tags(
        self: "ContentService", content_id: UUID, organization_id: str
    ) -> ContentTagsResponse:
        logger.info(f"Fetching tags for content {content_id}")
        primary_asset = self.session.exec(
            select(PrimaryAsset)
            .options(selectinload(PrimaryAsset.tags))
            .join(PrimaryAsset)
            .join(Version)
            .join(Node)
            .join(DerivedContent)
            .where(DerivedContent.id == content_id)
            .where(PrimaryAsset.organization_id == organization_id)
        ).first()

        if not primary_asset:
            logger.error(
                f"Primary asset {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Primary asset not found"
            )

        tag_results = [
            TagResult(
                id=tag.id,
                name=tag.name,
                color=tag.hex_color,
                created_at=tag.created_at,
                updated_at=tag.updated_at,
            )
            for tag in primary_asset.tags
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


def organization_bucket_from_organization_id(organization_id: str) -> str:
    """
    Generate the organization bucket name from the organization ID
    """
    return hashlib.sha256(organization_id.encode()).hexdigest()[:63]
