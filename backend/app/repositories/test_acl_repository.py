"""Unit tests for acl_repository functions."""

from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from app.repositories import acl_repository
from database.models import PrimaryAsset, PrimaryAssetRoleGrant, Team, User
from database.models_enums import PrimaryAssetKind, PrimaryAssetRole, PrincipalKind


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
    return "user-456"


@pytest.fixture
def asset_id() -> UUID:
    """Return a test primary asset ID."""
    return uuid4()


@pytest.fixture
def sample_grant(team_id: UUID, asset_id: UUID, org_id: str) -> PrimaryAssetRoleGrant:
    """Create a sample grant for testing."""
    return PrimaryAssetRoleGrant(
        id=uuid4(),
        primary_asset_id=asset_id,
        organization_id=org_id,
        principal_kind=PrincipalKind.team,
        team_id=team_id,
        user_id=None,
        role=PrimaryAssetRole.admin,
    )


@pytest.fixture
def sample_asset(asset_id: UUID, org_id: str) -> PrimaryAsset:
    """Create a sample primary asset for testing."""
    return PrimaryAsset(
        id=asset_id,
        organization_id=org_id,
        display_name="Test Codebase",
        kind=PrimaryAssetKind.CODEBASE,
    )


@pytest.fixture
def sample_user(user_id: str) -> User:
    """Create a sample user for testing."""
    return User(
        id=user_id,
        name="John Doe",
        email="john@example.com",
    )


@pytest.fixture
def sample_team(team_id: UUID, org_id: str) -> Team:
    """Create a sample team for testing."""
    return Team(
        id=team_id,
        organization_id=org_id,
        name="Engineering Team",
    )


class TestGetGrantByTeamAndAsset:
    """Tests for get_grant_by_team_and_asset function."""

    def test_returns_grant_when_found(
        self,
        session: MagicMock,
        sample_grant: PrimaryAssetRoleGrant,
        team_id: UUID,
        asset_id: UUID,
    ) -> None:
        """Should return grant when it exists."""
        session.exec.return_value.first.return_value = sample_grant

        result = acl_repository.get_grant_by_team_and_asset(
            session=session,
            team_id=team_id,
            primary_asset_id=asset_id,
        )

        assert result == sample_grant
        session.exec.assert_called_once()

    def test_returns_none_when_not_found(
        self, session: MagicMock, team_id: UUID, asset_id: UUID
    ) -> None:
        """Should return None when grant does not exist."""
        session.exec.return_value.first.return_value = None

        result = acl_repository.get_grant_by_team_and_asset(
            session=session,
            team_id=team_id,
            primary_asset_id=asset_id,
        )

        assert result is None
        session.exec.assert_called_once()


class TestGetGrantByUserAndAsset:
    """Tests for get_grant_by_user_and_asset function."""

    def test_returns_grant_when_found(
        self, session: MagicMock, user_id: str, asset_id: UUID, org_id: str
    ) -> None:
        """Should return grant when it exists."""
        grant = PrimaryAssetRoleGrant(
            id=uuid4(),
            primary_asset_id=asset_id,
            organization_id=org_id,
            principal_kind=PrincipalKind.user,
            user_id=user_id,
            team_id=None,
            role=PrimaryAssetRole.viewer,
        )
        session.exec.return_value.first.return_value = grant

        result = acl_repository.get_grant_by_user_and_asset(
            session=session,
            user_id=user_id,
            primary_asset_id=asset_id,
        )

        assert result == grant
        session.exec.assert_called_once()

    def test_returns_none_when_not_found(
        self, session: MagicMock, user_id: str, asset_id: UUID
    ) -> None:
        """Should return None when grant does not exist."""
        session.exec.return_value.first.return_value = None

        result = acl_repository.get_grant_by_user_and_asset(
            session=session,
            user_id=user_id,
            primary_asset_id=asset_id,
        )

        assert result is None
        session.exec.assert_called_once()


class TestGetTeamSourcesWithDetails:
    """Tests for get_team_sources_with_details function."""

    def test_returns_sources_with_details(
        self,
        session: MagicMock,
        sample_grant: PrimaryAssetRoleGrant,
        sample_asset: PrimaryAsset,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should return sources with grant and asset details."""
        session.exec.return_value.all.return_value = [(sample_grant, sample_asset)]

        result = acl_repository.get_team_sources_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            limit=30,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["grant"] == sample_grant
        assert result[0]["asset"] == sample_asset
        session.exec.assert_called_once()

    def test_filters_by_roles(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should filter by roles when provided."""
        session.exec.return_value.all.return_value = []

        acl_repository.get_team_sources_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            roles=["admin"],
            limit=30,
            offset=0,
        )

        session.exec.assert_called_once()

    def test_filters_by_search(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should filter by search query."""
        session.exec.return_value.all.return_value = []

        acl_repository.get_team_sources_with_details(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            search="test",
            limit=30,
            offset=0,
        )

        session.exec.assert_called_once()


class TestCountTeamSources:
    """Tests for count_team_sources function."""

    def test_returns_count(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should return count of team sources."""
        session.exec.return_value.one.return_value = 5

        result = acl_repository.count_team_sources(
            session=session,
            team_id=team_id,
            organization_id=org_id,
        )

        assert result == 5
        session.exec.assert_called_once()

    def test_filters_by_roles(
        self, session: MagicMock, team_id: UUID, org_id: str
    ) -> None:
        """Should filter by roles when provided."""
        session.exec.return_value.one.return_value = 3

        result = acl_repository.count_team_sources(
            session=session,
            team_id=team_id,
            organization_id=org_id,
            roles=["admin"],
        )

        assert result == 3
        session.exec.assert_called_once()


class TestGetSourceMembersWithDetails:
    """Tests for get_source_members_with_details function."""

    def test_returns_user_members(
        self,
        session: MagicMock,
        sample_asset: PrimaryAsset,
        sample_user: User,
        asset_id: UUID,
        org_id: str,
        user_id: str,
    ) -> None:
        """Should return user members with details."""
        grant = PrimaryAssetRoleGrant(
            id=uuid4(),
            primary_asset_id=asset_id,
            organization_id=org_id,
            principal_kind=PrincipalKind.user,
            user_id=user_id,
            team_id=None,
            role=PrimaryAssetRole.viewer,
        )

        # Mock the main query
        session.exec.return_value.all.return_value = [(grant, sample_asset)]

        # Mock the user lookup
        def exec_side_effect(query: Any) -> MagicMock:
            mock_result = MagicMock()
            mock_result.all.return_value = [(grant, sample_asset)]
            mock_result.first.return_value = sample_user
            return mock_result

        session.exec.side_effect = exec_side_effect

        result = acl_repository.get_source_members_with_details(
            session=session,
            primary_asset_id=asset_id,
            organization_id=org_id,
            limit=30,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["grant"] == grant
        assert result[0]["asset"] == sample_asset
        assert result[0]["kind"] == "user"
        assert result[0]["member"] == sample_user

    def test_filters_by_member_kind_user(
        self, session: MagicMock, asset_id: UUID, org_id: str
    ) -> None:
        """Should filter by user member kind."""
        session.exec.return_value.all.return_value = []

        result = acl_repository.get_source_members_with_details(
            session=session,
            primary_asset_id=asset_id,
            organization_id=org_id,
            member_kind="user",
            limit=30,
            offset=0,
        )

        assert result == []
        session.exec.assert_called()

    def test_filters_by_search(
        self, session: MagicMock, asset_id: UUID, org_id: str
    ) -> None:
        """Should filter by search query."""
        session.exec.return_value.all.return_value = []

        result = acl_repository.get_source_members_with_details(
            session=session,
            primary_asset_id=asset_id,
            organization_id=org_id,
            search="john",
            limit=30,
            offset=0,
        )

        assert result == []


class TestCountSourceMembers:
    """Tests for count_source_members function."""

    def test_returns_count(
        self, session: MagicMock, asset_id: UUID, org_id: str
    ) -> None:
        """Should return count of source members."""
        session.exec.return_value.all.return_value = []

        result = acl_repository.count_source_members(
            session=session,
            primary_asset_id=asset_id,
            organization_id=org_id,
        )

        assert result == 0


class TestCreateGrant:
    """Tests for create_grant function."""

    def test_creates_grant(
        self, session: MagicMock, sample_grant: PrimaryAssetRoleGrant
    ) -> None:
        """Should create a grant and return it."""
        result = acl_repository.create_grant(
            session=session,
            grant=sample_grant,
        )

        assert result == sample_grant
        session.add.assert_called_once_with(sample_grant)
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(sample_grant)


class TestDeleteGrant:
    """Tests for delete_grant function."""

    def test_deletes_grant(
        self, session: MagicMock, sample_grant: PrimaryAssetRoleGrant
    ) -> None:
        """Should delete a grant."""
        acl_repository.delete_grant(
            session=session,
            grant=sample_grant,
        )

        session.delete.assert_called_once_with(sample_grant)
        session.commit.assert_called_once()


class TestGetPrimaryAssetById:
    """Tests for get_primary_asset_by_id function."""

    def test_returns_asset_when_found(
        self,
        session: MagicMock,
        sample_asset: PrimaryAsset,
        asset_id: UUID,
        org_id: str,
    ) -> None:
        """Should return asset when it exists."""
        session.exec.return_value.first.return_value = sample_asset

        result = acl_repository.get_primary_asset_by_id(
            session=session,
            primary_asset_id=asset_id,
            organization_id=org_id,
        )

        assert result == sample_asset
        session.exec.assert_called_once()

    def test_returns_none_when_not_found(
        self, session: MagicMock, asset_id: UUID, org_id: str
    ) -> None:
        """Should return None when asset does not exist."""
        session.exec.return_value.first.return_value = None

        result = acl_repository.get_primary_asset_by_id(
            session=session,
            primary_asset_id=asset_id,
            organization_id=org_id,
        )

        assert result is None
        session.exec.assert_called_once()
