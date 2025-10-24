"""Unit tests for team_member_repository functions."""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from app.repositories import team_member_repository
from database.models import Team, TeamMembership, User
from database.models_enums import TeamRole


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
def user_id() -> str:
    """Return a test user ID."""
    return "user-123"


@pytest.fixture
def sample_team(team_id: UUID, org_id: str) -> Team:
    """Create a sample team."""
    return Team(
        id=team_id,
        organization_id=org_id,
        name="Engineering",
    )


@pytest.fixture
def sample_user(user_id: str) -> User:
    """Create a sample user."""
    return User(
        id=user_id,
        name="John Doe",
        email="john@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_membership(team_id: UUID, user_id: str) -> TeamMembership:
    """Create a sample team membership."""
    return TeamMembership(
        id=uuid4(),
        team_id=team_id,
        user_id=user_id,
        role=TeamRole.member,
    )


class TestGetTeamMembersWithDetails:
    """Tests for get_team_members_with_details function."""

    def test_returns_members_with_details(
        self,
        session: MagicMock,
        team_id: UUID,
        org_id: str,
        sample_membership: TeamMembership,
        sample_user: User,
        sample_team: Team,
    ) -> None:
        """Should return members with user and team details."""
        session.exec.return_value.all.return_value = [
            (sample_membership, sample_user, sample_team)
        ]

        result = team_member_repository.get_team_members_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        assert len(result) == 1
        assert result[0]["membership"] == sample_membership
        assert result[0]["user"] == sample_user
        assert result[0]["team"] == sample_team
        session.exec.assert_called_once()

    def test_filters_by_team_and_organization(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should filter by team_id and organization_id."""
        session.exec.return_value.all.return_value = []

        team_member_repository.get_team_members_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        session.exec.assert_called_once()

    def test_filters_by_roles(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should filter by role when provided."""
        session.exec.return_value.all.return_value = []

        team_member_repository.get_team_members_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            roles=["admin"],
        )

        session.exec.assert_called_once()

    def test_searches_by_name_or_email(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should search by name or email when provided."""
        session.exec.return_value.all.return_value = []

        team_member_repository.get_team_members_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            search="john",
        )

        session.exec.assert_called_once()

    def test_respects_pagination(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should apply limit and offset."""
        session.exec.return_value.all.return_value = []

        team_member_repository.get_team_members_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            limit=10,
            offset=5,
        )

        session.exec.assert_called_once()

    def test_returns_empty_list_when_no_members(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should return empty list when team has no members."""
        session.exec.return_value.all.return_value = []

        result = team_member_repository.get_team_members_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        assert result == []


class TestCountTeamMembers:
    """Tests for count_team_members function."""

    def test_returns_member_count(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should return count of team members."""
        session.exec.return_value.one.return_value = 5

        result = team_member_repository.count_team_members(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        assert result == 5
        session.exec.assert_called_once()

    def test_filters_by_team_and_organization(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should filter count by team_id and organization_id."""
        session.exec.return_value.one.return_value = 3

        team_member_repository.count_team_members(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        session.exec.assert_called_once()

    def test_counts_with_role_filter(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should count members with specific roles."""
        session.exec.return_value.one.return_value = 2

        result = team_member_repository.count_team_members(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            roles=["admin"],
        )

        assert result == 2
        session.exec.assert_called_once()

    def test_counts_with_search_filter(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should count members matching search query."""
        session.exec.return_value.one.return_value = 1

        result = team_member_repository.count_team_members(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            search="john",
        )

        assert result == 1
        session.exec.assert_called_once()


class TestGetMembership:
    """Tests for get_membership function."""

    def test_returns_membership_when_found(
        self,
        session: MagicMock,
        team_id: UUID,
        user_id: str,
        sample_membership: TeamMembership,
    ) -> None:
        """Should return membership when it exists."""
        session.exec.return_value.first.return_value = sample_membership

        result = team_member_repository.get_membership(
            session=session,
            team_id=team_id,
            user_id=user_id,
        )

        assert result == sample_membership
        session.exec.assert_called_once()

    def test_returns_none_when_not_found(
        self, session: MagicMock, team_id: UUID, user_id: str
    ) -> None:
        """Should return None when membership doesn't exist."""
        session.exec.return_value.first.return_value = None

        result = team_member_repository.get_membership(
            session=session,
            team_id=team_id,
            user_id=user_id,
        )

        assert result is None
        session.exec.assert_called_once()

    def test_filters_by_team_and_user(self, session: MagicMock, team_id: UUID) -> None:
        """Should filter by both team_id and user_id."""
        session.exec.return_value.first.return_value = None

        team_member_repository.get_membership(
            session=session,
            team_id=team_id,
            user_id="user-456",
        )

        session.exec.assert_called_once()


class TestCreateMembership:
    """Tests for create_membership function."""

    def test_creates_and_returns_membership(
        self, session: MagicMock, sample_membership: TeamMembership
    ) -> None:
        """Should add membership to session, commit, and return it."""
        result = team_member_repository.create_membership(
            session=session,
            membership=sample_membership,
        )

        session.add.assert_called_once_with(sample_membership)
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(sample_membership)
        assert result == sample_membership

    def test_commits_transaction(
        self, session: MagicMock, sample_membership: TeamMembership
    ) -> None:
        """Should commit the transaction."""
        team_member_repository.create_membership(
            session=session,
            membership=sample_membership,
        )

        session.commit.assert_called_once()


class TestDeleteMembership:
    """Tests for delete_membership function."""

    def test_deletes_membership(
        self, session: MagicMock, sample_membership: TeamMembership
    ) -> None:
        """Should delete membership from session and commit."""
        team_member_repository.delete_membership(
            session=session,
            membership=sample_membership,
        )

        session.delete.assert_called_once_with(sample_membership)
        session.commit.assert_called_once()

    def test_commits_transaction(
        self, session: MagicMock, sample_membership: TeamMembership
    ) -> None:
        """Should commit the transaction."""
        team_member_repository.delete_membership(
            session=session,
            membership=sample_membership,
        )

        session.commit.assert_called_once()


class TestRoleMapping:
    """Tests for role mapping helper function."""

    def test_maps_admin_role(self) -> None:
        """Should map 'admin' to TeamRole.team_admin."""
        result = team_member_repository._map_frontend_role_to_backend("admin")
        assert result == TeamRole.team_admin

    def test_maps_member_role(self) -> None:
        """Should map 'member' to TeamRole.member."""
        result = team_member_repository._map_frontend_role_to_backend("member")
        assert result == TeamRole.member
