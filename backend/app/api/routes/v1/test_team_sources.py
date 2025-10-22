"""Unit tests for team_sources API routes."""

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.api.routes.v1 import team_sources
from app.schemas.source_access_schema import (
    AddTeamSourcesRequest,
    RemoveTeamSourcesRequest,
    TeamSourceInput,
    TeamSourceResponse,
    TeamSourcesResponse,
    UpdateTeamSourcesRequest,
)


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


@pytest.fixture
def team_id() -> UUID:
    """Return a test team ID."""
    return uuid4()


@pytest.fixture
def source_id() -> UUID:
    """Return a test source ID."""
    return uuid4()


class TestGetTeamSources:
    """Tests for get_team_sources endpoint."""

    @patch("app.api.routes.v1.team_sources.SourceAccessService")
    def test_returns_team_sources(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        team_id: UUID,
        source_id: UUID,
    ) -> None:
        """Should return team sources successfully."""
        mock_service = mock_service_class.return_value
        mock_service.get_team_sources.return_value = TeamSourcesResponse(
            sources=[
                TeamSourceResponse(
                    id=str(source_id),
                    organization_id="org-123",
                    kind="CODEBASE",
                    display_name="Test Repo",
                    provider="GITHUB",
                    created_at="2025-01-01T00:00:00",
                    updated_at="2025-01-01T00:00:00",
                    role="admin",
                    visibility="private",
                    team_id=str(team_id),
                )
            ],
            total=1,
        )

        response = team_sources.get_team_sources(
            session=session,
            user=user,
            team_id=team_id,
            limit=30,
            offset=0,
        )

        assert response.total == 1
        assert len(response.sources) == 1
        mock_service.get_team_sources.assert_called_once()

    @patch("app.api.routes.v1.team_sources.SourceAccessService")
    def test_handles_filters(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        team_id: UUID,
    ) -> None:
        """Should pass filters to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_team_sources.return_value = TeamSourcesResponse(
            sources=[], total=0
        )

        team_sources.get_team_sources(
            session=session,
            user=user,
            team_id=team_id,
            roles=["admin"],
            visibilities=["private"],
            search="test",
        )

        mock_service.get_team_sources.assert_called_once_with(
            team_id=team_id,
            organization_id=user.organization_id,
            roles=["admin"],
            visibilities=["private"],
            search="test",
            limit=30,
            offset=0,
        )


class TestAddTeamSources:
    """Tests for add_team_sources endpoint."""

    @patch("app.api.routes.v1.team_sources.SourceAccessService")
    def test_adds_sources_successfully(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        team_id: UUID,
        source_id: UUID,
    ) -> None:
        """Should add sources to team successfully."""
        mock_service = mock_service_class.return_value

        request = AddTeamSourcesRequest(
            sources=[TeamSourceInput(source_id=str(source_id), role="admin")]
        )

        result = team_sources.add_team_sources(
            session=session,
            user=user,
            team_id=team_id,
            request=request,
        )

        assert result is None
        mock_service.add_team_sources.assert_called_once_with(
            team_id=team_id,
            organization_id=user.organization_id,
            request=request,
        )


class TestUpdateTeamSources:
    """Tests for update_team_sources endpoint."""

    @patch("app.api.routes.v1.team_sources.SourceAccessService")
    def test_updates_sources_successfully(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        team_id: UUID,
        source_id: UUID,
    ) -> None:
        """Should update source roles successfully."""
        mock_service = mock_service_class.return_value

        request = UpdateTeamSourcesRequest(
            sources=[TeamSourceInput(source_id=str(source_id), role="member")]
        )

        result = team_sources.update_team_sources(
            session=session,
            user=user,
            team_id=team_id,
            request=request,
        )

        assert result is None
        mock_service.update_team_sources.assert_called_once_with(
            team_id=team_id,
            organization_id=user.organization_id,
            request=request,
        )


class TestRemoveTeamSources:
    """Tests for remove_team_sources endpoint."""

    @patch("app.api.routes.v1.team_sources.SourceAccessService")
    def test_removes_sources_successfully(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        team_id: UUID,
        source_id: UUID,
    ) -> None:
        """Should remove sources from team successfully."""
        mock_service = mock_service_class.return_value

        request = RemoveTeamSourcesRequest(source_ids=[str(source_id)])

        result = team_sources.remove_team_sources(
            session=session,
            user=user,
            team_id=team_id,
            request=request,
        )

        assert result is None
        mock_service.remove_team_sources.assert_called_once_with(
            team_id=team_id,
            organization_id=user.organization_id,
            request=request,
        )
