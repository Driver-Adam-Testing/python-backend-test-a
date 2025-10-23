"""Unit tests for admin_sources API routes."""

from unittest.mock import MagicMock, patch

import pytest

from app.api.routes.v1 import admin_sources
from app.schemas.admin_sources_schema import AdminSourceRecord, AdminSourcesResponse


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def user() -> MagicMock:
    """Create a mock user token."""
    user = MagicMock()
    user.user_id = "user-123"
    user.organization_id = "org-123"
    return user


class TestGetAdminSources:
    """Tests for get_admin_sources endpoint."""

    @patch("app.api.routes.v1.admin_sources.AdminSourcesService")
    def test_returns_admin_sources(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should return admin sources with counts."""
        mock_service = mock_service_class.return_value
        mock_service.get_admin_sources.return_value = AdminSourcesResponse(
            results=[
                AdminSourceRecord(
                    id="asset-123",
                    organization_id="org-123",
                    kind="CODEBASE",
                    display_name="Test Codebase",
                    provider="GITHUB",
                    created_at="2025-01-01T00:00:00",
                    updated_at="2025-10-23T00:00:00",
                    visibility="private",
                    members_count=5,
                    teams_count=2,
                    tags=None,
                ),
            ],
            total_count=1,
        )

        response = admin_sources.get_admin_sources(
            session=session,
            user=user,
            limit=20,
            offset=0,
            search=None,
            kind=None,
            tag_ids=None,
            sort_by="updated_at",
            sort_direction="DESC",
        )

        assert isinstance(response, AdminSourcesResponse)
        assert len(response.results) == 1
        assert response.total_count == 1
        assert response.results[0].members_count == 5
        assert response.results[0].teams_count == 2

    @patch("app.api.routes.v1.admin_sources.AdminSourcesService")
    def test_passes_correct_parameters_to_service(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should pass all parameters correctly to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_admin_sources.return_value = AdminSourcesResponse(
            results=[],
            total_count=0,
        )

        admin_sources.get_admin_sources(
            session=session,
            user=user,
            limit=50,
            offset=10,
            search="test",
            kind=["CODEBASE", "FILE"],
            tag_ids=["tag-1", "tag-2"],
            sort_by="created_at",
            sort_direction="ASC",
        )

        mock_service.get_admin_sources.assert_called_once_with(
            organization_id="org-123",
            search="test",
            kinds=["CODEBASE", "FILE"],
            tag_ids=["tag-1", "tag-2"],
            sort_by="created_at",
            sort_direction="ASC",
            limit=50,
            offset=10,
        )

    @patch("app.api.routes.v1.admin_sources.AdminSourcesService")
    def test_uses_default_pagination_values(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should use default values for pagination."""
        mock_service = mock_service_class.return_value
        mock_service.get_admin_sources.return_value = AdminSourcesResponse(
            results=[],
            total_count=0,
        )

        admin_sources.get_admin_sources(
            session=session,
            user=user,
            limit=20,
            offset=0,
            search=None,
            kind=None,
            tag_ids=None,
            sort_by="updated_at",
            sort_direction="DESC",
        )

        call_kwargs = mock_service.get_admin_sources.call_args.kwargs
        assert call_kwargs["limit"] == 20
        assert call_kwargs["offset"] == 0
        assert call_kwargs["sort_by"] == "updated_at"
        assert call_kwargs["sort_direction"] == "DESC"

    @patch("app.api.routes.v1.admin_sources.AdminSourcesService")
    def test_returns_empty_when_no_sources(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should return empty list when no sources found."""
        mock_service = mock_service_class.return_value
        mock_service.get_admin_sources.return_value = AdminSourcesResponse(
            results=[],
            total_count=0,
        )

        response = admin_sources.get_admin_sources(
            session=session,
            user=user,
            limit=20,
            offset=0,
            search="nonexistent",
            kind=None,
            tag_ids=None,
            sort_by="updated_at",
            sort_direction="DESC",
        )

        assert len(response.results) == 0
        assert response.total_count == 0

    @patch("app.api.routes.v1.admin_sources.AdminSourcesService")
    def test_handles_search_filter(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should pass search filter to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_admin_sources.return_value = AdminSourcesResponse(
            results=[],
            total_count=0,
        )

        admin_sources.get_admin_sources(
            session=session,
            user=user,
            limit=20,
            offset=0,
            search="codebase",
            kind=None,
            tag_ids=None,
            sort_by="updated_at",
            sort_direction="DESC",
        )

        call_kwargs = mock_service.get_admin_sources.call_args.kwargs
        assert call_kwargs["search"] == "codebase"

    @patch("app.api.routes.v1.admin_sources.AdminSourcesService")
    def test_handles_kind_filter(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should pass kind filter to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_admin_sources.return_value = AdminSourcesResponse(
            results=[],
            total_count=0,
        )

        admin_sources.get_admin_sources(
            session=session,
            user=user,
            limit=20,
            offset=0,
            search=None,
            kind=["CODEBASE"],
            tag_ids=None,
            sort_by="updated_at",
            sort_direction="DESC",
        )

        call_kwargs = mock_service.get_admin_sources.call_args.kwargs
        assert call_kwargs["kinds"] == ["CODEBASE"]

    @patch("app.api.routes.v1.admin_sources.AdminSourcesService")
    def test_handles_tag_filter(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should pass tag filter to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_admin_sources.return_value = AdminSourcesResponse(
            results=[],
            total_count=0,
        )

        admin_sources.get_admin_sources(
            session=session,
            user=user,
            limit=20,
            offset=0,
            search=None,
            kind=None,
            tag_ids=["tag-1", "tag-2"],
            sort_by="updated_at",
            sort_direction="DESC",
        )

        call_kwargs = mock_service.get_admin_sources.call_args.kwargs
        assert call_kwargs["tag_ids"] == ["tag-1", "tag-2"]

    @patch("app.api.routes.v1.admin_sources.AdminSourcesService")
    def test_handles_sorting(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should pass sorting parameters to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_admin_sources.return_value = AdminSourcesResponse(
            results=[],
            total_count=0,
        )

        admin_sources.get_admin_sources(
            session=session,
            user=user,
            limit=20,
            offset=0,
            search=None,
            kind=None,
            tag_ids=None,
            sort_by="display_name",
            sort_direction="ASC",
        )

        call_kwargs = mock_service.get_admin_sources.call_args.kwargs
        assert call_kwargs["sort_by"] == "display_name"
        assert call_kwargs["sort_direction"] == "ASC"
