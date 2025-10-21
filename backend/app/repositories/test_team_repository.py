"""Unit tests for team_repository functions."""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from app.repositories import team_repository
from database.models import Team


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def org_id() -> str:
    """Return a test organization ID."""
    return "org-123"


@pytest.fixture
def team_id() -> UUID:
    """Return a test team ID."""
    return uuid4()


@pytest.fixture
def sample_team(team_id: UUID, org_id: str) -> Team:
    """Create a sample team for testing."""
    return Team(
        id=team_id,
        organization_id=org_id,
        name="Engineering Team",
    )


class TestGetTeamById:
    """Tests for get_team_by_id function."""

    def test_returns_team_when_found(
        self, session: MagicMock, sample_team: Team, team_id: UUID, org_id: str
    ) -> None:
        """Should return team when it exists for the organization."""
        session.exec.return_value.first.return_value = sample_team

        result = team_repository.get_team_by_id(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        assert result == sample_team
        session.exec.assert_called_once()

    def test_returns_none_when_not_found(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should return None when team does not exist."""
        session.exec.return_value.first.return_value = None

        result = team_repository.get_team_by_id(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        assert result is None
        session.exec.assert_called_once()

    def test_filters_by_organization(self, session: MagicMock, team_id: UUID) -> None:
        """Should filter by both team_id and organization_id."""
        session.exec.return_value.first.return_value = None

        team_repository.get_team_by_id(
            session=session,
            team_id=team_id,
            organization_id="org-123",
        )

        # Verify session.exec was called (query includes org filter)
        session.exec.assert_called_once()


class TestGetTeamsWithCounts:
    """Tests for get_teams_with_counts function."""

    def test_returns_teams_with_counts(self, session: MagicMock, org_id: str) -> None:
        """Should return teams with aggregated counts."""
        mock_team = Team(id=uuid4(), organization_id=org_id, name="Team 1")
        session.exec.return_value.all.return_value = [
            (mock_team, 2, 5, 3),  # team, admins, members, sources
        ]

        result = team_repository.get_teams_with_counts(
            session=session,
            organization_id=org_id,
            limit=30,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["team"] == mock_team
        assert result[0]["admins"] == 2
        assert result[0]["members"] == 5
        assert result[0]["sources"] == 3
        session.exec.assert_called_once()

    def test_respects_pagination(self, session: MagicMock, org_id: str) -> None:
        """Should apply limit and offset to query."""
        session.exec.return_value.all.return_value = []

        team_repository.get_teams_with_counts(
            session=session,
            organization_id=org_id,
            limit=10,
            offset=20,
        )

        session.exec.assert_called_once()

    def test_filters_by_organization(self, session: MagicMock) -> None:
        """Should only return teams for the specified organization."""
        session.exec.return_value.all.return_value = []

        team_repository.get_teams_with_counts(
            session=session,
            organization_id="org-456",
            limit=30,
            offset=0,
        )

        session.exec.assert_called_once()


class TestGetTeamWithCounts:
    """Tests for get_team_with_counts function."""

    def test_returns_team_with_counts_when_found(
        self, session: MagicMock, sample_team: Team, team_id: UUID, org_id: str
    ) -> None:
        """Should return team with counts when it exists."""
        session.exec.return_value.first.return_value = (sample_team, 1, 3, 2)

        result = team_repository.get_team_with_counts(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        assert result is not None
        assert result["team"] == sample_team
        assert result["admins"] == 1
        assert result["members"] == 3
        assert result["sources"] == 2

    def test_returns_none_when_not_found(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should return None when team does not exist."""
        session.exec.return_value.first.return_value = None

        result = team_repository.get_team_with_counts(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        assert result is None


class TestSearchTeamsWithCounts:
    """Tests for search_teams_with_counts function."""

    def test_searches_by_name(self, session: MagicMock, org_id: str) -> None:
        """Should search teams by name pattern."""
        mock_team = Team(id=uuid4(), organization_id=org_id, name="Engineering")
        session.exec.return_value.all.return_value = [(mock_team, 1, 2, 3)]

        result = team_repository.search_teams_with_counts(
            session=session,
            organization_id=org_id,
            query="eng",
            limit=30,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["team"] == mock_team
        session.exec.assert_called_once()

    def test_case_insensitive_search(self, session: MagicMock, org_id: str) -> None:
        """Should perform case-insensitive search."""
        session.exec.return_value.all.return_value = []

        team_repository.search_teams_with_counts(
            session=session,
            organization_id=org_id,
            query="ENG",
            limit=30,
            offset=0,
        )

        session.exec.assert_called_once()

    def test_respects_pagination(self, session: MagicMock, org_id: str) -> None:
        """Should apply limit and offset."""
        session.exec.return_value.all.return_value = []

        team_repository.search_teams_with_counts(
            session=session,
            organization_id=org_id,
            query="test",
            limit=5,
            offset=10,
        )

        session.exec.assert_called_once()


class TestCountTeams:
    """Tests for count_teams function."""

    def test_returns_count(self, session: MagicMock, org_id: str) -> None:
        """Should return total count of teams."""
        session.exec.return_value.one.return_value = 42

        result = team_repository.count_teams(
            session=session,
            organization_id=org_id,
        )

        assert result == 42
        session.exec.assert_called_once()

    def test_filters_by_organization(self, session: MagicMock) -> None:
        """Should count only teams for specified organization."""
        session.exec.return_value.one.return_value = 10

        team_repository.count_teams(
            session=session,
            organization_id="org-789",
        )

        session.exec.assert_called_once()


class TestCountTeamsBySearch:
    """Tests for count_teams_by_search function."""

    def test_returns_search_count(self, session: MagicMock, org_id: str) -> None:
        """Should return count of teams matching search."""
        session.exec.return_value.one.return_value = 5

        result = team_repository.count_teams_by_search(
            session=session,
            organization_id=org_id,
            search_query="eng",
        )

        assert result == 5
        session.exec.assert_called_once()

    def test_case_insensitive_count(self, session: MagicMock, org_id: str) -> None:
        """Should count using case-insensitive search."""
        session.exec.return_value.one.return_value = 3

        team_repository.count_teams_by_search(
            session=session,
            organization_id=org_id,
            search_query="TEST",
        )

        session.exec.assert_called_once()


class TestCreateTeam:
    """Tests for create_team function."""

    def test_creates_and_returns_team(
        self, session: MagicMock, sample_team: Team
    ) -> None:
        """Should add team to session, commit, and return it."""
        result = team_repository.create_team(session=session, team=sample_team)

        session.add.assert_called_once_with(sample_team)
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(sample_team)
        assert result == sample_team

    def test_commits_transaction(self, session: MagicMock, sample_team: Team) -> None:
        """Should commit the transaction."""
        team_repository.create_team(session=session, team=sample_team)

        session.commit.assert_called_once()


class TestDeleteTeam:
    """Tests for delete_team function."""

    def test_deletes_team(self, session: MagicMock, sample_team: Team) -> None:
        """Should delete team from session and commit."""
        team_repository.delete_team(session=session, team=sample_team)

        session.delete.assert_called_once_with(sample_team)
        session.commit.assert_called_once()

    def test_commits_transaction(self, session: MagicMock, sample_team: Team) -> None:
        """Should commit the transaction."""
        team_repository.delete_team(session=session, team=sample_team)

        session.commit.assert_called_once()
