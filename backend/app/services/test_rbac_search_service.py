"""Unit tests for RBAC Search Service."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.rbac_search_schema import MemberSearchItem, MemberSearchResponse
from app.services.rbac_search_service import (
    RBACSearchService,
    count_teams_in_organization,
    count_users_in_organization,
    search_teams_in_organization,
    search_users_in_organization,
)


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def organization_id() -> str:
    """Return a test organization ID."""
    return "org-123"


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock user."""
    user = MagicMock()
    user.id = "user-123"
    user.name = "John Doe"
    user.email = "john@example.com"
    return user


@pytest.fixture
def mock_team() -> MagicMock:
    """Create a mock team."""
    team = MagicMock()
    team.id = uuid4()
    team.name = "Engineering Team"
    return team


class TestSearchUsersInOrganization:
    """Tests for search_users_in_organization function."""

    @patch("app.services.rbac_search_service.select")
    def test_searches_users_by_name(
        self, mock_select: MagicMock, session: MagicMock, organization_id: str
    ) -> None:
        """Should search users by name."""
        mock_query_result = MagicMock()
        mock_query_result.all.return_value = []
        session.exec.return_value = mock_query_result

        search_users_in_organization(
            session=session,
            organization_id=organization_id,
            query="john",
            limit=30,
        )

        session.exec.assert_called_once()

    @patch("app.services.rbac_search_service.select")
    def test_returns_matching_users(
        self,
        mock_select: MagicMock,
        session: MagicMock,
        organization_id: str,
        mock_user: MagicMock,
    ) -> None:
        """Should return users matching search query."""
        mock_query_result = MagicMock()
        mock_query_result.all.return_value = [mock_user]
        session.exec.return_value = mock_query_result

        result = search_users_in_organization(
            session=session,
            organization_id=organization_id,
            query="john",
            limit=30,
        )

        assert len(result) == 1
        assert result[0] == mock_user


class TestSearchTeamsInOrganization:
    """Tests for search_teams_in_organization function."""

    @patch("app.services.rbac_search_service.select")
    def test_searches_teams_by_name(
        self, mock_select: MagicMock, session: MagicMock, organization_id: str
    ) -> None:
        """Should search teams by name."""
        mock_query_result = MagicMock()
        mock_query_result.all.return_value = []
        session.exec.return_value = mock_query_result

        search_teams_in_organization(
            session=session,
            organization_id=organization_id,
            query="eng",
            limit=30,
        )

        session.exec.assert_called_once()

    @patch("app.services.rbac_search_service.select")
    def test_returns_matching_teams(
        self,
        mock_select: MagicMock,
        session: MagicMock,
        organization_id: str,
        mock_team: MagicMock,
    ) -> None:
        """Should return teams matching search query."""
        mock_query_result = MagicMock()
        mock_query_result.all.return_value = [mock_team]
        session.exec.return_value = mock_query_result

        result = search_teams_in_organization(
            session=session,
            organization_id=organization_id,
            query="eng",
            limit=30,
        )

        assert len(result) == 1
        assert result[0] == mock_team


class TestCountUsersInOrganization:
    """Tests for count_users_in_organization function."""

    @patch("app.services.rbac_search_service.select")
    def test_counts_matching_users(
        self, mock_select: MagicMock, session: MagicMock, organization_id: str
    ) -> None:
        """Should count users matching search query."""
        mock_query_result = MagicMock()
        mock_query_result.one.return_value = 5
        session.exec.return_value = mock_query_result

        result = count_users_in_organization(
            session=session,
            organization_id=organization_id,
            query="john",
        )

        assert result == 5
        session.exec.assert_called_once()


class TestCountTeamsInOrganization:
    """Tests for count_teams_in_organization function."""

    @patch("app.services.rbac_search_service.select")
    def test_counts_matching_teams(
        self, mock_select: MagicMock, session: MagicMock, organization_id: str
    ) -> None:
        """Should count teams matching search query."""
        mock_query_result = MagicMock()
        mock_query_result.one.return_value = 3
        session.exec.return_value = mock_query_result

        result = count_teams_in_organization(
            session=session,
            organization_id=organization_id,
            query="eng",
        )

        assert result == 3
        session.exec.assert_called_once()


class TestRBACSearchServiceSearchMembers:
    """Tests for RBACSearchService.search_members method."""

    @patch("app.services.rbac_search_service.count_teams_in_organization")
    @patch("app.services.rbac_search_service.count_users_in_organization")
    @patch("app.services.rbac_search_service.search_teams_in_organization")
    @patch("app.services.rbac_search_service.search_users_in_organization")
    def test_combines_users_and_teams(
        self,
        mock_search_users: MagicMock,
        mock_search_teams: MagicMock,
        mock_count_users: MagicMock,
        mock_count_teams: MagicMock,
        session: MagicMock,
        organization_id: str,
        mock_user: MagicMock,
        mock_team: MagicMock,
    ) -> None:
        """Should combine and return both users and teams in search results."""
        mock_search_users.return_value = [mock_user]
        mock_search_teams.return_value = [mock_team]
        mock_count_users.return_value = 1
        mock_count_teams.return_value = 1

        service = RBACSearchService(session)
        result = service.search_members(
            organization_id=organization_id,
            query="test",
            limit=30,
            offset=0,
        )

        assert isinstance(result, MemberSearchResponse)
        assert len(result.items) == 2
        assert result.total == 2

    @patch("app.services.rbac_search_service.count_teams_in_organization")
    @patch("app.services.rbac_search_service.count_users_in_organization")
    @patch("app.services.rbac_search_service.search_teams_in_organization")
    @patch("app.services.rbac_search_service.search_users_in_organization")
    def test_sorts_results_by_name(
        self,
        mock_search_users: MagicMock,
        mock_search_teams: MagicMock,
        mock_count_users: MagicMock,
        mock_count_teams: MagicMock,
        session: MagicMock,
        organization_id: str,
    ) -> None:
        """Should sort combined results alphabetically by name."""
        user1 = MagicMock()
        user1.id = "user-1"
        user1.name = "Zara Smith"
        user1.email = "zara@example.com"

        user2 = MagicMock()
        user2.id = "user-2"
        user2.name = "Alice Johnson"
        user2.email = "alice@example.com"

        team = MagicMock()
        team.id = uuid4()
        team.name = "Beta Team"

        mock_search_users.return_value = [user1, user2]
        mock_search_teams.return_value = [team]
        mock_count_users.return_value = 2
        mock_count_teams.return_value = 1

        service = RBACSearchService(session)
        result = service.search_members(
            organization_id=organization_id,
            query="test",
            limit=30,
            offset=0,
        )

        assert len(result.items) == 3
        assert result.items[0].name == "Alice Johnson"
        assert result.items[1].name == "Beta Team"
        assert result.items[2].name == "Zara Smith"

    @patch("app.services.rbac_search_service.count_teams_in_organization")
    @patch("app.services.rbac_search_service.count_users_in_organization")
    @patch("app.services.rbac_search_service.search_teams_in_organization")
    @patch("app.services.rbac_search_service.search_users_in_organization")
    def test_applies_pagination(
        self,
        mock_search_users: MagicMock,
        mock_search_teams: MagicMock,
        mock_count_users: MagicMock,
        mock_count_teams: MagicMock,
        session: MagicMock,
        organization_id: str,
    ) -> None:
        """Should apply offset and limit to combined results."""
        users = []
        for i in range(5):
            user = MagicMock()
            user.id = f"user-{i}"
            user.name = f"User {i:02d}"
            user.email = f"user{i}@example.com"
            users.append(user)

        mock_search_users.return_value = users
        mock_search_teams.return_value = []
        mock_count_users.return_value = 5
        mock_count_teams.return_value = 0

        service = RBACSearchService(session)
        result = service.search_members(
            organization_id=organization_id,
            query="user",
            limit=2,
            offset=1,
        )

        assert len(result.items) == 2
        assert result.total == 5
        assert result.items[0].name == "User 01"
        assert result.items[1].name == "User 02"

    @patch("app.services.rbac_search_service.count_teams_in_organization")
    @patch("app.services.rbac_search_service.count_users_in_organization")
    @patch("app.services.rbac_search_service.search_teams_in_organization")
    @patch("app.services.rbac_search_service.search_users_in_organization")
    def test_user_items_have_correct_fields(
        self,
        mock_search_users: MagicMock,
        mock_search_teams: MagicMock,
        mock_count_users: MagicMock,
        mock_count_teams: MagicMock,
        session: MagicMock,
        organization_id: str,
        mock_user: MagicMock,
    ) -> None:
        """Should return user items with correct fields."""
        mock_search_users.return_value = [mock_user]
        mock_search_teams.return_value = []
        mock_count_users.return_value = 1
        mock_count_teams.return_value = 0

        service = RBACSearchService(session)
        result = service.search_members(
            organization_id=organization_id,
            query="john",
            limit=30,
            offset=0,
        )

        assert len(result.items) == 1
        user_item = result.items[0]
        assert isinstance(user_item, MemberSearchItem)
        assert user_item.member_id == "user-123"
        assert user_item.kind == "user"
        assert user_item.name == "John Doe"
        assert user_item.email == "john@example.com"
        assert user_item.picture == ""

    @patch("app.services.rbac_search_service.count_teams_in_organization")
    @patch("app.services.rbac_search_service.count_users_in_organization")
    @patch("app.services.rbac_search_service.search_teams_in_organization")
    @patch("app.services.rbac_search_service.search_users_in_organization")
    def test_team_items_have_correct_fields(
        self,
        mock_search_users: MagicMock,
        mock_search_teams: MagicMock,
        mock_count_users: MagicMock,
        mock_count_teams: MagicMock,
        session: MagicMock,
        organization_id: str,
        mock_team: MagicMock,
    ) -> None:
        """Should return team items with correct fields."""
        mock_search_users.return_value = []
        mock_search_teams.return_value = [mock_team]
        mock_count_users.return_value = 0
        mock_count_teams.return_value = 1

        service = RBACSearchService(session)
        result = service.search_members(
            organization_id=organization_id,
            query="eng",
            limit=30,
            offset=0,
        )

        assert len(result.items) == 1
        team_item = result.items[0]
        assert isinstance(team_item, MemberSearchItem)
        assert team_item.member_id == str(mock_team.id)
        assert team_item.kind == "team"
        assert team_item.name == "Engineering Team"
        assert team_item.email is None
        assert team_item.picture is None

    @patch("app.services.rbac_search_service.count_teams_in_organization")
    @patch("app.services.rbac_search_service.count_users_in_organization")
    @patch("app.services.rbac_search_service.search_teams_in_organization")
    @patch("app.services.rbac_search_service.search_users_in_organization")
    def test_returns_empty_when_no_matches(
        self,
        mock_search_users: MagicMock,
        mock_search_teams: MagicMock,
        mock_count_users: MagicMock,
        mock_count_teams: MagicMock,
        session: MagicMock,
        organization_id: str,
    ) -> None:
        """Should return empty list when no matches found."""
        mock_search_users.return_value = []
        mock_search_teams.return_value = []
        mock_count_users.return_value = 0
        mock_count_teams.return_value = 0

        service = RBACSearchService(session)
        result = service.search_members(
            organization_id=organization_id,
            query="nonexistent",
            limit=30,
            offset=0,
        )

        assert len(result.items) == 0
        assert result.total == 0
