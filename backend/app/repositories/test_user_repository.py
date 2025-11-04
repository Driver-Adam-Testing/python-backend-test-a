"""Unit tests for user_repository functions."""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from app.repositories import user_repository
from database.models import (
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Team,
    TeamMembership,
    User,
)
from database.models_enums import (
    PrimaryAssetKind,
    PrimaryAssetRole,
    TeamRole,
)


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def org_id() -> str:
    """Return a test organization ID."""
    return "org-123"


@pytest.fixture
def user_id() -> str:
    """Return a test user ID."""
    return "user-456"


@pytest.fixture
def team_id() -> UUID:
    """Return a test team ID."""
    return uuid4()


@pytest.fixture
def asset_id() -> UUID:
    """Return a test primary asset ID."""
    return uuid4()


@pytest.fixture
def sample_user(user_id: str) -> User:
    """Create a sample user for testing."""
    return User(
        id=user_id,
        name="John Doe",
        email="john@example.com",
        created_at=datetime.utcnow(),
        auth0_updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_team(team_id: UUID, org_id: str) -> Team:
    """Create a sample team for testing."""
    return Team(
        id=team_id,
        organization_id=org_id,
        name="Engineering Team",
    )


@pytest.fixture
def sample_membership(user_id: str, team_id: UUID) -> TeamMembership:
    """Create a sample team membership for testing."""
    return TeamMembership(
        id=uuid4(),
        team_id=team_id,
        user_id=user_id,
        role=TeamRole.team_admin,
    )


@pytest.fixture
def sample_asset(asset_id: UUID, org_id: str) -> PrimaryAsset:
    """Create a sample primary asset for testing."""
    return PrimaryAsset(
        id=asset_id,
        organization_id=org_id,
        display_name="Test Codebase",
        kind=PrimaryAssetKind.CODEBASE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_grant(user_id: str, asset_id: UUID, org_id: str) -> PrimaryAssetRoleGrant:
    """Create a sample grant for testing."""
    return PrimaryAssetRoleGrant(
        id=uuid4(),
        primary_asset_id=asset_id,
        organization_id=org_id,
        user_id=user_id,
        role=PrimaryAssetRole.asset_admin,
    )


class TestSearchOrganizationUsers:
    """Tests for search_organization_users function."""

    def test_returns_users_matching_query(
        self, session: MagicMock, sample_user: User, org_id: str
    ) -> None:
        """Should return users matching search query."""
        session.exec.return_value.all.return_value = [sample_user]

        result = user_repository.search_organization_users(
            session=session,
            organization_id=org_id,
            query="john",
            limit=30,
            offset=0,
        )

        assert result == [sample_user]
        session.exec.assert_called_once()

    def test_returns_empty_list_when_no_matches(
        self, session: MagicMock, org_id: str
    ) -> None:
        """Should return empty list when no users match."""
        session.exec.return_value.all.return_value = []

        result = user_repository.search_organization_users(
            session=session,
            organization_id=org_id,
            query="nonexistent",
            limit=30,
            offset=0,
        )

        assert result == []
        session.exec.assert_called_once()


class TestCountOrganizationUsers:
    """Tests for count_organization_users function."""

    def test_returns_count_of_matching_users(
        self, session: MagicMock, org_id: str
    ) -> None:
        """Should return count of users matching query."""
        session.exec.return_value.one.return_value = 5

        result = user_repository.count_organization_users(
            session=session,
            organization_id=org_id,
            query="john",
        )

        assert result == 5
        session.exec.assert_called_once()


class TestGetUserTeamsWithDetails:
    """Tests for get_user_teams_with_details function."""

    def test_returns_teams_with_counts(
        self,
        session: MagicMock,
        user_id: str,
        org_id: str,
        sample_membership: TeamMembership,
        sample_team: Team,
    ) -> None:
        """Should return teams with membership and count details."""
        session.exec.return_value.all.return_value = [
            (sample_membership, sample_team, 2, 3, 5)
        ]

        result = user_repository.get_user_teams_with_details(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            roles=None,
            search=None,
            limit=30,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["membership"] == sample_membership
        assert result[0]["team"] == sample_team
        assert result[0]["admins"] == 2
        assert result[0]["members"] == 3
        assert result[0]["sources"] == 5
        session.exec.assert_called_once()

    def test_filters_by_role(
        self, session: MagicMock, user_id: str, org_id: str
    ) -> None:
        """Should filter teams by role."""
        session.exec.return_value.all.return_value = []

        result = user_repository.get_user_teams_with_details(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            roles=["admin"],
            search=None,
            limit=30,
            offset=0,
        )

        assert result == []
        session.exec.assert_called_once()

    def test_filters_by_search(
        self, session: MagicMock, user_id: str, org_id: str
    ) -> None:
        """Should filter teams by search query."""
        session.exec.return_value.all.return_value = []

        result = user_repository.get_user_teams_with_details(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            roles=None,
            search="engineering",
            limit=30,
            offset=0,
        )

        assert result == []
        session.exec.assert_called_once()


class TestCountUserTeams:
    """Tests for count_user_teams function."""

    def test_returns_count_of_teams(
        self, session: MagicMock, user_id: str, org_id: str
    ) -> None:
        """Should return count of user's teams."""
        session.exec.return_value.one.return_value = 3

        result = user_repository.count_user_teams(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            roles=None,
            search=None,
        )

        assert result == 3
        session.exec.assert_called_once()


class TestGetUserTeamMembership:
    """Tests for get_user_team_membership function."""

    def test_returns_membership_when_found(
        self,
        session: MagicMock,
        user_id: str,
        team_id: UUID,
        sample_membership: TeamMembership,
    ) -> None:
        """Should return membership when it exists."""
        session.exec.return_value.first.return_value = sample_membership

        result = user_repository.get_user_team_membership(
            session=session,
            user_id=user_id,
            team_id=team_id,
        )

        assert result == sample_membership
        session.exec.assert_called_once()

    def test_returns_none_when_not_found(
        self, session: MagicMock, user_id: str, team_id: UUID
    ) -> None:
        """Should return None when membership does not exist."""
        session.exec.return_value.first.return_value = None

        result = user_repository.get_user_team_membership(
            session=session,
            user_id=user_id,
            team_id=team_id,
        )

        assert result is None
        session.exec.assert_called_once()


class TestCreateUserTeamMembership:
    """Tests for create_user_team_membership function."""

    def test_creates_and_returns_membership(
        self, session: MagicMock, sample_membership: TeamMembership
    ) -> None:
        """Should create membership and return it."""
        result = user_repository.create_user_team_membership(
            session=session,
            membership=sample_membership,
        )

        assert result == sample_membership
        session.add.assert_called_once_with(sample_membership)
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(sample_membership)


class TestDeleteUserTeamMembership:
    """Tests for delete_user_team_membership function."""

    def test_deletes_membership(
        self, session: MagicMock, sample_membership: TeamMembership
    ) -> None:
        """Should delete membership."""
        user_repository.delete_user_team_membership(
            session=session,
            membership=sample_membership,
        )

        session.delete.assert_called_once_with(sample_membership)
        session.commit.assert_called_once()


class TestGetUserSourcesWithDetails:
    """Tests for get_user_sources_with_details function."""

    def test_returns_sources_with_assets(
        self,
        session: MagicMock,
        user_id: str,
        org_id: str,
        sample_grant: PrimaryAssetRoleGrant,
        sample_asset: PrimaryAsset,
    ) -> None:
        """Should return sources with grant and asset details."""
        session.exec.return_value.all.return_value = [(sample_grant, sample_asset)]

        result = user_repository.get_user_sources_with_details(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            roles=None,
            search=None,
            limit=30,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["grant"] == sample_grant
        assert result[0]["asset"] == sample_asset
        session.exec.assert_called_once()

    def test_filters_by_role(
        self, session: MagicMock, user_id: str, org_id: str
    ) -> None:
        """Should filter sources by role."""
        session.exec.return_value.all.return_value = []

        result = user_repository.get_user_sources_with_details(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            roles=["admin"],
            search=None,
            limit=30,
            offset=0,
        )

        assert result == []
        session.exec.assert_called_once()

    def test_filters_by_search(
        self, session: MagicMock, user_id: str, org_id: str
    ) -> None:
        """Should filter sources by search query."""
        session.exec.return_value.all.return_value = []

        result = user_repository.get_user_sources_with_details(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            roles=None,
            search="codebase",
            limit=30,
            offset=0,
        )

        assert result == []
        session.exec.assert_called_once()


class TestCountUserSources:
    """Tests for count_user_sources function."""

    def test_returns_count_of_sources(
        self, session: MagicMock, user_id: str, org_id: str
    ) -> None:
        """Should return count of user's sources."""
        session.exec.return_value.one.return_value = 7

        result = user_repository.count_user_sources(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            roles=None,
            search=None,
        )

        assert result == 7
        session.exec.assert_called_once()


class TestGetUserSourceGrant:
    """Tests for get_user_source_grant function."""

    def test_returns_grant_when_found(
        self,
        session: MagicMock,
        user_id: str,
        asset_id: UUID,
        sample_grant: PrimaryAssetRoleGrant,
    ) -> None:
        """Should return grant when it exists."""
        session.exec.return_value.first.return_value = sample_grant

        result = user_repository.get_user_source_grant(
            session=session,
            user_id=user_id,
            primary_asset_id=asset_id,
        )

        assert result == sample_grant
        session.exec.assert_called_once()

    def test_returns_none_when_not_found(
        self, session: MagicMock, user_id: str, asset_id: UUID
    ) -> None:
        """Should return None when grant does not exist."""
        session.exec.return_value.first.return_value = None

        result = user_repository.get_user_source_grant(
            session=session,
            user_id=user_id,
            primary_asset_id=asset_id,
        )

        assert result is None
        session.exec.assert_called_once()


class TestCreateUserSourceGrant:
    """Tests for create_user_source_grant function."""

    def test_creates_and_returns_grant(
        self, session: MagicMock, sample_grant: PrimaryAssetRoleGrant
    ) -> None:
        """Should create grant and return it."""
        result = user_repository.create_user_source_grant(
            session=session,
            grant=sample_grant,
        )

        assert result == sample_grant
        session.add.assert_called_once_with(sample_grant)
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(sample_grant)


class TestDeleteUserSourceGrant:
    """Tests for delete_user_source_grant function."""

    def test_deletes_grant(
        self, session: MagicMock, sample_grant: PrimaryAssetRoleGrant
    ) -> None:
        """Should delete grant."""
        user_repository.delete_user_source_grant(
            session=session,
            grant=sample_grant,
        )

        session.delete.assert_called_once_with(sample_grant)
        session.commit.assert_called_once()
