"""Service for Admin Sources business logic."""

import logging
from uuid import UUID

from sqlmodel import Session

from app.auth.models import User
from app.repositories import admin_sources_repository
from app.schemas.admin_sources_schema import (
    AdminSourceRecord,
    AdminSourcesResponse,
    SourceVisibility,
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
        visibility: list[SourceVisibility] | None = None,
        sort_by: str = "updated_at",
        sort_direction: str = "DESC",
        limit: int = 20,
        offset: int = 0,
        check_user_id: str | None = None,
        check_team_id: UUID | None = None,
    ) -> AdminSourcesResponse:
        """
        Get paginated list of sources with admin metadata.

        Args:
            user: Authenticated user making the request
            search: Optional search query for display_name
            kinds: Optional list of asset kinds to filter
            tag_ids: Optional list of tag IDs to filter
            visibility: Optional list of visibility levels to filter
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
            visibility=visibility,
            sort_by=sort_by,
            sort_direction=sort_direction,
            limit=limit,
            offset=offset,
            check_user_id=check_user_id,
            check_team_id=check_team_id,
        )

        # Get total count
        total_count = admin_sources_repository.count_sources(
            session=self.session,
            user_id=user.user_id,
            organization_id=organization_id,
            search=search,
            kinds=kinds,
            tag_ids=tag_ids,
            visibility=visibility,
        )

        # Build response records
        results = [self._build_admin_source_record(data) for data in source_data]

        logger.info(f"Found {len(results)} sources (total: {total_count})")

        return AdminSourcesResponse(
            results=results,
            total_count=total_count,
        )

    def _build_admin_source_record(self, data: dict) -> AdminSourceRecord:
        asset = data["asset"]
        members_count = data["members_count"]
        teams_count = data["teams_count"]
        visibility = data["visibility"]
        status = data.get("status")
        has_user_access = data.get("has_user_access", False)
        has_team_access = data.get("has_team_access", False)

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
            status=status,
            members_count=members_count,
            teams_count=teams_count,
            tags=None,  # TODO: Add tags if needed
            has_user_access=has_user_access,
            has_team_access=has_team_access,
        )
