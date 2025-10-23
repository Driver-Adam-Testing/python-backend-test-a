"""Unit tests for user_teams API routes."""

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.api.routes.v1 import user_teams
from app.schemas.user_schema import (
    AddUserTeamsRequest,
    OrganizationMembersResponse,
    RemoveUserTeamsRequest,
    UpdateUserTeamsRequest,
    UserResponse,
    UserTeamInput,
    UserTeamResponse,
    UserTeamsResponse,
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
def team_id() -> UUID:
    """Return a test team ID."""
    return uuid4()


class TestSearchOrganizationUsers:
    """Tests for search_organization_users endpoint."""

    @patch("app.api.routes.v1.user_teams.UserService")
    def test_returns_search_results(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
    ) -> None:
        """Should return organization users matching search query."""
        mock_service = mock_service_class.return_value
        mock_service.search_organization_users.return_value = (
            OrganizationMembersResponse(
                members=[
                    UserResponse(
                        user_id=user_id,
                        name="John Doe",
                        email="john@example.com",
                        picture="",
                    )
                ],
                total=1,
            )
        )

        response = user_teams.search_organization_users(
            session=session,
            user=user,
            query="john",
            limit=30,
            offset=0,
        )

        assert response.total == 1
        assert len(response.members) == 1
        assert response.members[0].user_id == user_id
        mock_service.search_organization_users.assert_called_once_with(
            organization_id="org-123",
            query="john",
            limit=30,
            offset=0,
        )

    @patch("app.api.routes.v1.user_teams.UserService")
    def test_handles_pagination(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should pass pagination parameters to service."""
        mock_service = mock_service_class.return_value
        mock_service.search_organization_users.return_value = (
            OrganizationMembersResponse(
                members=[],
                total=0,
            )
        )

        user_teams.search_organization_users(
            session=session,
            user=user,
            query="test",
            limit=50,
            offset=10,
        )

        mock_service.search_organization_users.assert_called_once_with(
            organization_id="org-123",
            query="test",
            limit=50,
            offset=10,
        )


class TestGetUserTeams:
    """Tests for get_user_teams endpoint."""

    @patch("app.api.routes.v1.user_teams.UserService")
    def test_returns_user_teams(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
        team_id: UUID,
    ) -> None:
        """Should return user's teams successfully."""
        mock_service = mock_service_class.return_value
        mock_service.get_user_teams.return_value = UserTeamsResponse(
            teams=[
                UserTeamResponse(
                    id=str(team_id),
                    name="Engineering",
                    admins=2,
                    members=5,
                    sources=10,
                    created_at="2025-01-01T00:00:00",
                    updated_at="2025-01-01T00:00:00",
                    role="admin",
                )
            ],
            total=1,
        )

        response = user_teams.get_user_teams(
            session=session,
            user=user,
            user_id=user_id,
            limit=30,
            offset=0,
        )

        assert response.total == 1
        assert len(response.teams) == 1
        assert response.teams[0].role == "admin"
        mock_service.get_user_teams.assert_called_once()

    @patch("app.api.routes.v1.user_teams.UserService")
    def test_handles_filters(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
    ) -> None:
        """Should pass filters to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_user_teams.return_value = UserTeamsResponse(
            teams=[],
            total=0,
        )

        user_teams.get_user_teams(
            session=session,
            user=user,
            user_id=user_id,
            limit=30,
            offset=0,
            roles=["admin"],
            search="engineering",
        )

        mock_service.get_user_teams.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            roles=["admin"],
            search="engineering",
            limit=30,
            offset=0,
        )


class TestAddUserTeams:
    """Tests for add_user_teams endpoint."""

    @patch("app.api.routes.v1.user_teams.UserService")
    def test_adds_user_to_teams(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
        team_id: UUID,
    ) -> None:
        """Should add user to teams successfully."""
        mock_service = mock_service_class.return_value
        mock_service.add_user_teams.return_value = None

        request = AddUserTeamsRequest(
            teams=[UserTeamInput(team_id=str(team_id), role="admin")]
        )

        user_teams.add_user_teams(
            session=session,
            user=user,
            user_id=user_id,
            request=request,
        )

        mock_service.add_user_teams.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            request=request,
        )


class TestUpdateUserTeams:
    """Tests for update_user_teams endpoint."""

    @patch("app.api.routes.v1.user_teams.UserService")
    def test_updates_user_team_roles(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
        team_id: UUID,
    ) -> None:
        """Should update user's team roles successfully."""
        mock_service = mock_service_class.return_value
        mock_service.update_user_teams.return_value = None

        request = UpdateUserTeamsRequest(
            teams=[UserTeamInput(team_id=str(team_id), role="member")]
        )

        user_teams.update_user_teams(
            session=session,
            user=user,
            user_id=user_id,
            request=request,
        )

        mock_service.update_user_teams.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            request=request,
        )


class TestRemoveUserTeams:
    """Tests for remove_user_teams endpoint."""

    @patch("app.api.routes.v1.user_teams.UserService")
    def test_removes_user_from_teams(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        user_id: str,
        team_id: UUID,
    ) -> None:
        """Should remove user from teams successfully."""
        mock_service = mock_service_class.return_value
        mock_service.remove_user_teams.return_value = None

        request = RemoveUserTeamsRequest(team_ids=[str(team_id)])

        user_teams.remove_user_teams(
            session=session,
            user=user,
            user_id=user_id,
            request=request,
        )

        mock_service.remove_user_teams.assert_called_once_with(
            user_id=user_id,
            organization_id="org-123",
            request=request,
        )
