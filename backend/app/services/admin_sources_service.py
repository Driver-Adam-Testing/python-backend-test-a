"""Service for Admin Sources business logic."""

import logging

from sqlmodel import Session

from app.auth.models import User
from app.repositories import admin_sources_repository
from app.schemas.admin_sources_schema import (
    AdminSourceRecord,
    AdminSourcesResponse,
)

logger = logging.getLogger(__name__)


class AdminSourcesService:
    """Service for Admin Sources operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_admin_sources(
        self,
        user: User,
        search: str | None = None,
        kinds: list[str] | None = None,
        tag_ids: list[str] | None = None,
        sort_by: str = "updated_at",
        sort_direction: str = "DESC",
        limit: int = 20,
        offset: int = 0,
    ) -> AdminSourcesResponse:
        """
        Get paginated list of sources with admin metadata.

        Args:
            user: Authenticated user making the request
            search: Optional search query for display_name
            kinds: Optional list of asset kinds to filter
            tag_ids: Optional list of tag IDs to filter
            sort_by: Field to sort by
            sort_direction: Sort direction (ASC/DESC)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            AdminSourcesResponse with sources and counts
        """
        organization_id = user.organization_id
        logger.info(
            f"Getting admin sources for organization {organization_id} by user {user.user_id} "
            f"(limit={limit}, offset={offset}, search={search})"
        )

        # Get sources with counts
        source_data = admin_sources_repository.get_sources_with_counts(
            session=self.session,
            user_id=user.user_id,
            organization_id=organization_id,
            search=search,
            kinds=kinds,
            tag_ids=tag_ids,
            sort_by=sort_by,
            sort_direction=sort_direction,
            limit=limit,
            offset=offset,
        )

        # Get total count
        total_count = admin_sources_repository.count_sources(
            session=self.session,
            user_id=user.user_id,
            organization_id=organization_id,
            search=search,
            kinds=kinds,
            tag_ids=tag_ids,
        )

        # Build response records
        results = [self._build_admin_source_record(data) for data in source_data]

        logger.info(f"Found {len(results)} sources (total: {total_count})")

        return AdminSourcesResponse(
            results=results,
            total_count=total_count,
        )

    def _build_admin_source_record(self, data: dict) -> AdminSourceRecord:
        """Build AdminSourceRecord from repository data."""
        asset = data["asset"]
        members_count = data["members_count"]
        teams_count = data["teams_count"]

        # Determine visibility (default to private for now)
        # TODO: Get actual visibility from PrimaryAssetRoleGrant when field is added
        visibility = "private"

        return AdminSourceRecord(
            id=str(asset.id),
            organization_id=asset.organization_id,
            kind=asset.kind.value if hasattr(asset.kind, "value") else str(asset.kind),
            display_name=asset.display_name,
            provider=(
                asset.provider.value
                if asset.provider and hasattr(asset.provider, "value")
                else None
            ),
            created_at=asset.created_at.isoformat(),
            updated_at=asset.updated_at.isoformat(),
            visibility=visibility,
            members_count=members_count,
            teams_count=teams_count,
            tags=None,  # TODO: Add tags if needed
        )
