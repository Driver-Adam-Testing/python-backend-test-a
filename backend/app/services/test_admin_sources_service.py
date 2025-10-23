"""Unit tests for AdminSourcesService."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.admin_sources_schema import AdminSourceRecord, AdminSourcesResponse
from app.services.admin_sources_service import AdminSourcesService


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def organization_id() -> str:
    """Return a test organization ID."""
    return "org-123"


@pytest.fixture
def mock_asset() -> MagicMock:
    """Create a mock primary asset."""
    asset = MagicMock()
    asset.id = uuid4()
    asset.organization_id = "org-123"
    asset.kind = MagicMock()
    asset.kind.value = "CODEBASE"
    asset.display_name = "Test Codebase"
    asset.provider = MagicMock()
    asset.provider.value = "GITHUB"
    asset.created_at = datetime(2025, 1, 1)
    asset.updated_at = datetime(2025, 10, 23)
    return asset


class TestGetAdminSources:
    """Tests for AdminSourcesService.get_admin_sources method."""

    @patch("app.services.admin_sources_service.admin_sources_repository")
    def test_returns_sources_with_counts(
        self,
        mock_repo: MagicMock,
        session: MagicMock,
        organization_id: str,
        mock_asset: MagicMock,
    ) -> None:
        """Should return sources with member and team counts."""
        mock_repo.get_sources_with_counts.return_value = [
            {
                "asset": mock_asset,
                "members_count": 5,
                "teams_count": 2,
            }
        ]
        mock_repo.count_sources.return_value = 1

        service = AdminSourcesService(session)
        result = service.get_admin_sources(
            organization_id=organization_id,
            limit=20,
            offset=0,
        )

        assert isinstance(result, AdminSourcesResponse)
        assert len(result.results) == 1
        assert result.total_count == 1
        assert result.results[0].members_count == 5
        assert result.results[0].teams_count == 2

    @patch("app.services.admin_sources_service.admin_sources_repository")
    def test_passes_correct_parameters_to_repository(
        self,
        mock_repo: MagicMock,
        session: MagicMock,
        organization_id: str,
    ) -> None:
        """Should pass all parameters correctly to repository."""
        mock_repo.get_sources_with_counts.return_value = []
        mock_repo.count_sources.return_value = 0

        service = AdminSourcesService(session)
        service.get_admin_sources(
            organization_id=organization_id,
            search="test",
            kinds=["CODEBASE", "FILE"],
            tag_ids=["tag-1", "tag-2"],
            sort_by="created_at",
            sort_direction="ASC",
            limit=50,
            offset=10,
        )

        mock_repo.get_sources_with_counts.assert_called_once_with(
            session=session,
            organization_id=organization_id,
            search="test",
            kinds=["CODEBASE", "FILE"],
            tag_ids=["tag-1", "tag-2"],
            sort_by="created_at",
            sort_direction="ASC",
            limit=50,
            offset=10,
        )

        mock_repo.count_sources.assert_called_once_with(
            session=session,
            organization_id=organization_id,
            search="test",
            kinds=["CODEBASE", "FILE"],
            tag_ids=["tag-1", "tag-2"],
        )

    @patch("app.services.admin_sources_service.admin_sources_repository")
    def test_uses_default_parameters(
        self,
        mock_repo: MagicMock,
        session: MagicMock,
        organization_id: str,
    ) -> None:
        """Should use default values for optional parameters."""
        mock_repo.get_sources_with_counts.return_value = []
        mock_repo.count_sources.return_value = 0

        service = AdminSourcesService(session)
        service.get_admin_sources(organization_id=organization_id)

        call_kwargs = mock_repo.get_sources_with_counts.call_args.kwargs
        assert call_kwargs["search"] is None
        assert call_kwargs["kinds"] is None
        assert call_kwargs["tag_ids"] is None
        assert call_kwargs["sort_by"] == "updated_at"
        assert call_kwargs["sort_direction"] == "DESC"
        assert call_kwargs["limit"] == 20
        assert call_kwargs["offset"] == 0

    @patch("app.services.admin_sources_service.admin_sources_repository")
    def test_returns_empty_when_no_sources(
        self,
        mock_repo: MagicMock,
        session: MagicMock,
        organization_id: str,
    ) -> None:
        """Should return empty list when no sources found."""
        mock_repo.get_sources_with_counts.return_value = []
        mock_repo.count_sources.return_value = 0

        service = AdminSourcesService(session)
        result = service.get_admin_sources(
            organization_id=organization_id,
        )

        assert len(result.results) == 0
        assert result.total_count == 0

    @patch("app.services.admin_sources_service.admin_sources_repository")
    def test_handles_multiple_sources(
        self,
        mock_repo: MagicMock,
        session: MagicMock,
        organization_id: str,
    ) -> None:
        """Should handle multiple sources correctly."""
        assets = []
        for i in range(3):
            asset = MagicMock()
            asset.id = uuid4()
            asset.organization_id = organization_id
            asset.kind = MagicMock()
            asset.kind.value = "CODEBASE"
            asset.display_name = f"Codebase {i}"
            asset.provider = None
            asset.created_at = datetime(2025, 1, 1)
            asset.updated_at = datetime(2025, 10, 23)
            assets.append(asset)

        mock_repo.get_sources_with_counts.return_value = [
            {"asset": assets[0], "members_count": 5, "teams_count": 2},
            {"asset": assets[1], "members_count": 3, "teams_count": 1},
            {"asset": assets[2], "members_count": 0, "teams_count": 0},
        ]
        mock_repo.count_sources.return_value = 3

        service = AdminSourcesService(session)
        result = service.get_admin_sources(
            organization_id=organization_id,
        )

        assert len(result.results) == 3
        assert result.total_count == 3
        assert result.results[0].members_count == 5
        assert result.results[1].members_count == 3
        assert result.results[2].members_count == 0


class TestBuildAdminSourceRecord:
    """Tests for AdminSourcesService._build_admin_source_record method."""

    def test_builds_record_with_all_fields(
        self,
        session: MagicMock,
        mock_asset: MagicMock,
    ) -> None:
        """Should build complete admin source record."""
        data = {
            "asset": mock_asset,
            "members_count": 10,
            "teams_count": 3,
        }

        service = AdminSourcesService(session)
        result = service._build_admin_source_record(data)

        assert isinstance(result, AdminSourceRecord)
        assert result.id == str(mock_asset.id)
        assert result.organization_id == "org-123"
        assert result.kind == "CODEBASE"
        assert result.display_name == "Test Codebase"
        assert result.provider == "GITHUB"
        assert result.visibility == "private"
        assert result.members_count == 10
        assert result.teams_count == 3

    def test_handles_asset_without_provider(
        self,
        session: MagicMock,
        mock_asset: MagicMock,
    ) -> None:
        """Should handle assets without provider."""
        mock_asset.provider = None
        data = {
            "asset": mock_asset,
            "members_count": 0,
            "teams_count": 0,
        }

        service = AdminSourcesService(session)
        result = service._build_admin_source_record(data)

        assert result.provider is None

    def test_handles_zero_counts(
        self,
        session: MagicMock,
        mock_asset: MagicMock,
    ) -> None:
        """Should handle zero member and team counts."""
        data = {
            "asset": mock_asset,
            "members_count": 0,
            "teams_count": 0,
        }

        service = AdminSourcesService(session)
        result = service._build_admin_source_record(data)

        assert result.members_count == 0
        assert result.teams_count == 0

    def test_converts_timestamps_to_iso(
        self,
        session: MagicMock,
        mock_asset: MagicMock,
    ) -> None:
        """Should convert datetime timestamps to ISO format."""
        data = {
            "asset": mock_asset,
            "members_count": 5,
            "teams_count": 2,
        }

        service = AdminSourcesService(session)
        result = service._build_admin_source_record(data)

        assert "2025-01-01" in result.created_at
        assert "2025-10-23" in result.updated_at
