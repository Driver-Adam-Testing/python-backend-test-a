"""Unit tests for user_sources API routes."""

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.api.routes.v1 import user_sources
from app.schemas.user_schema import (
    AddUserSourcesRequest,
    RemoveUserSourcesRequest,
    UpdateUserSourcesRequest,
    UserSourceInput,
    UserSourceResponse,
    UserSourcesResponse,
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
def user_id() -> str:
    """Return a test user ID."""
    return "user-456"


@pytest.fixture
def source_id() -> UUID:
    """Return a test source ID."""
    return uuid4()


class TestGetUserSources:
    """Tests for get_user_sources endpoint."""

    @patch("app.api.routes.v1.user_sources.UserService")
    def test_returns_user_sources(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
        source_id: UUID,
    ) -> None:
        """Should return user's sources successfully."""
        mock_service = mock_service_class.return_value
        mock_service.get_user_sources.return_value = UserSourcesResponse(
            sources=[
                UserSourceResponse(
                    id=str(source_id),
                    organization_id="org-123",
                    kind="CODEBASE",
                    display_name="Test Repo",
                    provider="GITHUB",
                    created_at="2025-01-01T00:00:00",
                    updated_at="2025-01-01T00:00:00",
                    role="admin",
                    visibility="private",
                    user_id=user_id,
                )
            ],
            total=1,
        )

        response = user_sources.get_user_sources(
            session=session,
            user=user,
            user_id=user_id,
            limit=30,
            offset=0,
        )

        assert response.total == 1
        assert len(response.sources) == 1
        assert response.sources[0].role == "admin"
        assert response.sources[0].user_id == user_id
        mock_service.get_user_sources.assert_called_once()

    @patch("app.api.routes.v1.user_sources.UserService")
    def test_handles_filters(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
    ) -> None:
        """Should pass filters to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_user_sources.return_value = UserSourcesResponse(
            sources=[],
            total=0,
        )

        user_sources.get_user_sources(
            session=session,
            user=user,
            user_id=user_id,
            limit=30,
            offset=0,
            roles=["admin"],
            search="codebase",
        )

        mock_service.get_user_sources.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            roles=["admin"],
            search="codebase",
            limit=30,
            offset=0,
        )

    @patch("app.api.routes.v1.user_sources.UserService")
    def test_handles_pagination(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
    ) -> None:
        """Should pass pagination parameters to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_user_sources.return_value = UserSourcesResponse(
            sources=[],
            total=0,
        )

        user_sources.get_user_sources(
            session=session,
            user=user,
            user_id=user_id,
            limit=50,
            offset=20,
        )

        mock_service.get_user_sources.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            roles=None,
            search=None,
            limit=50,
            offset=20,
        )


class TestAddUserSources:
    """Tests for add_user_sources endpoint."""

    @patch("app.api.routes.v1.user_sources.UserService")
    def test_adds_user_sources(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
        source_id: UUID,
    ) -> None:
        """Should add user sources successfully."""
        mock_service = mock_service_class.return_value
        mock_service.add_user_sources.return_value = None

        request = AddUserSourcesRequest(
            sources=[UserSourceInput(source_id=str(source_id), role="admin")]
        )

        user_sources.add_user_sources(
            session=session,
            user=user,
            user_id=user_id,
            request=request,
        )

        mock_service.add_user_sources.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            request=request,
        )


class TestUpdateUserSources:
    """Tests for update_user_sources endpoint."""

    @patch("app.api.routes.v1.user_sources.UserService")
    def test_updates_user_source_roles(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
        source_id: UUID,
    ) -> None:
        """Should update user's source roles successfully."""
        mock_service = mock_service_class.return_value
        mock_service.update_user_sources.return_value = None

        request = UpdateUserSourcesRequest(
            sources=[UserSourceInput(source_id=str(source_id), role="member")]
        )

        user_sources.update_user_sources(
            session=session,
            user=user,
            user_id=user_id,
            request=request,
        )

        mock_service.update_user_sources.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            request=request,
        )


class TestRemoveUserSources:
    """Tests for remove_user_sources endpoint."""

    @patch("app.api.routes.v1.user_sources.UserService")
    def test_removes_user_sources(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
        source_id: UUID,
    ) -> None:
        """Should remove user sources successfully."""
        mock_service = mock_service_class.return_value
        mock_service.remove_user_sources.return_value = None

        request = RemoveUserSourcesRequest(source_ids=[str(source_id)])

        user_sources.remove_user_sources(
            session=session,
            user=user,
            user_id=user_id,
            request=request,
        )

        mock_service.remove_user_sources.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            request=request,
        )
