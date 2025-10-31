"""Unit tests for UserService business logic."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from database.models import (
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Team,
    TeamMembership,
    User,
)
from database.models_enums import (
    PrimaryAssetKind,
    PrimaryAssetProvider,
    PrimaryAssetRole,
    TeamRole,
)
from fastapi import HTTPException

from app.schemas.user_schema import (
    AddUserSourcesRequest,
    AddUserTeamsRequest,
    RemoveUserSourcesRequest,
    RemoveUserTeamsRequest,
    UpdateUserSourcesRequest,
    UpdateUserTeamsRequest,
    UserSourceInput,
    UserTeamInput,
)
from app.services.user_service import UserService


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    mock = MagicMock()
    mock.get.return_value = None
    return mock


@pytest.fixture
def service(session: MagicMock) -> UserService:
    """Create a UserService instance."""
    return UserService(session)


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
    """Create a sample user."""
    return User(
        id=user_id,
        name="John Doe",
        email="john@example.com",
        created_at=datetime.utcnow(),
        auth0_updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_team(team_id: UUID, org_id: str) -> Team:
    """Create a sample team."""
    return Team(
        id=team_id,
        organization_id=org_id,
        name="Engineering",
    )


@pytest.fixture
def sample_asset(asset_id: UUID, org_id: str) -> PrimaryAsset:
    """Create a sample primary asset."""
    asset = PrimaryAsset(
        id=asset_id,
        organization_id=org_id,
        display_name="Test Codebase",
        kind=PrimaryAssetKind.CODEBASE,
        provider=PrimaryAssetProvider.GITHUB,
    )
    asset.created_at = datetime.utcnow()
    asset.updated_at = datetime.utcnow()
    return asset


@pytest.fixture
def sample_membership(user_id: str, team_id: UUID) -> TeamMembership:
    """Create a sample team membership."""
    return TeamMembership(
        id=uuid4(),
        team_id=team_id,
        user_id=user_id,
        role=TeamRole.team_admin,
    )


@pytest.fixture
def sample_grant(user_id: str, asset_id: UUID, org_id: str) -> PrimaryAssetRoleGrant:
    """Create a sample grant."""
    return PrimaryAssetRoleGrant(
        id=uuid4(),
        primary_asset_id=asset_id,
        organization_id=org_id,
        user_id=user_id,
        role=PrimaryAssetRole.asset_admin,
    )


class TestSearchOrganizationUsers:
    """Tests for search_organization_users method."""

    @patch("app.services.user_service.user_repository")
    def test_returns_search_results(
        self,
        mock_repo: MagicMock,
        service: UserService,
        org_id: str,
        sample_user: User,
    ) -> None:
        """Should return search results with users and total count."""
        mock_repo.search_organization_users.return_value = [sample_user]
        mock_repo.count_organization_users.return_value = 1

        result = service.search_organization_users(
            organization_id=org_id,
            query="john",
            limit=30,
            offset=0,
        )

        assert len(result.members) == 1
        assert result.members[0].user_id == sample_user.id
        assert result.members[0].name == sample_user.name
        assert result.members[0].email == sample_user.email
        assert result.total == 1


class TestGetUserTeams:
    """Tests for get_user_teams method."""

    @patch("app.services.user_service.user_repository")
    def test_returns_user_teams(
        self,
        mock_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        sample_team: Team,
        sample_membership: TeamMembership,
    ) -> None:
        """Should return user's teams with role and count information."""
        team_data = {
            "membership": sample_membership,
            "team": sample_team,
            "admins": 2,
            "members": 3,
            "sources": 5,
        }
        mock_repo.get_user_teams_with_details.return_value = [team_data]
        mock_repo.count_user_teams.return_value = 1

        result = service.get_user_teams(
            user_id=user_id,
            organization_id=org_id,
            roles=None,
            search=None,
            limit=30,
            offset=0,
        )

        assert len(result.teams) == 1
        assert result.teams[0].id == str(sample_team.id)
        assert result.teams[0].name == sample_team.name
        assert result.teams[0].admins == 2
        assert result.teams[0].members == 3
        assert result.teams[0].sources == 5
        assert result.teams[0].role == "admin"
        assert result.total == 1


class TestAddUserTeams:
    """Tests for add_user_teams method."""

    @patch("app.services.user_service.user_repository")
    @patch("app.services.user_service.team_repository")
    def test_adds_user_to_teams(
        self,
        mock_team_repo: MagicMock,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        team_id: UUID,
        sample_team: Team,
    ) -> None:
        """Should add user to teams successfully."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_user_repo.get_user_team_membership.return_value = None

        request = AddUserTeamsRequest(
            teams=[UserTeamInput(team_id=str(team_id), role="admin")]
        )

        service.add_user_teams(
            user_id=user_id,
            organization_id=org_id,
            request=request,
        )

        mock_user_repo.create_user_team_membership.assert_called_once()

    @patch("app.services.user_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_team_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        team_id: UUID,
    ) -> None:
        """Should raise 404 when team not found."""
        mock_team_repo.get_team_by_id.return_value = None

        request = AddUserTeamsRequest(
            teams=[UserTeamInput(team_id=str(team_id), role="admin")]
        )

        with pytest.raises(HTTPException) as exc_info:
            service.add_user_teams(
                user_id=user_id,
                organization_id=org_id,
                request=request,
            )

        assert exc_info.value.status_code == 404

    @patch("app.services.user_service.user_repository")
    @patch("app.services.user_service.team_repository")
    def test_raises_409_when_membership_exists(
        self,
        mock_team_repo: MagicMock,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        team_id: UUID,
        sample_team: Team,
        sample_membership: TeamMembership,
    ) -> None:
        """Should raise 409 when user already in team."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_user_repo.get_user_team_membership.return_value = sample_membership

        request = AddUserTeamsRequest(
            teams=[UserTeamInput(team_id=str(team_id), role="admin")]
        )

        with pytest.raises(HTTPException) as exc_info:
            service.add_user_teams(
                user_id=user_id,
                organization_id=org_id,
                request=request,
            )

        assert exc_info.value.status_code == 409


class TestUpdateUserTeams:
    """Tests for update_user_teams method."""

    @patch("app.services.user_service.user_repository")
    @patch("app.services.user_service.team_repository")
    def test_updates_user_team_roles(
        self,
        mock_team_repo: MagicMock,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        team_id: UUID,
        sample_team: Team,
        sample_membership: TeamMembership,
    ) -> None:
        """Should update user's team roles successfully."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_user_repo.get_user_team_membership.return_value = sample_membership

        request = UpdateUserTeamsRequest(
            teams=[UserTeamInput(team_id=str(team_id), role="member")]
        )

        service.update_user_teams(
            user_id=user_id,
            organization_id=org_id,
            request=request,
        )

        assert sample_membership.role == TeamRole.team_member
        service.session.add.assert_called_once_with(sample_membership)
        service.session.commit.assert_called_once()

    @patch("app.services.user_service.user_repository")
    @patch("app.services.user_service.team_repository")
    def test_raises_404_when_membership_not_found(
        self,
        mock_team_repo: MagicMock,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        team_id: UUID,
        sample_team: Team,
    ) -> None:
        """Should raise 404 when user not in team."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_user_repo.get_user_team_membership.return_value = None

        request = UpdateUserTeamsRequest(
            teams=[UserTeamInput(team_id=str(team_id), role="member")]
        )

        with pytest.raises(HTTPException) as exc_info:
            service.update_user_teams(
                user_id=user_id,
                organization_id=org_id,
                request=request,
            )

        assert exc_info.value.status_code == 404


class TestRemoveUserTeams:
    """Tests for remove_user_teams method."""

    @patch("app.services.user_service.user_repository")
    @patch("app.services.user_service.team_repository")
    def test_removes_user_from_teams(
        self,
        mock_team_repo: MagicMock,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        team_id: UUID,
        sample_team: Team,
        sample_membership: TeamMembership,
    ) -> None:
        """Should remove user from teams successfully."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_user_repo.get_user_team_membership.return_value = sample_membership

        request = RemoveUserTeamsRequest(team_ids=[str(team_id)])

        service.remove_user_teams(
            user_id=user_id,
            organization_id=org_id,
            request=request,
        )

        mock_user_repo.delete_user_team_membership.assert_called_once_with(
            session=service.session,
            membership=sample_membership,
        )


class TestGetUserSources:
    """Tests for get_user_sources method."""

    @patch("app.services.user_service.user_repository")
    def test_returns_user_sources(
        self,
        mock_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        sample_asset: PrimaryAsset,
        sample_grant: PrimaryAssetRoleGrant,
    ) -> None:
        """Should return user's sources with role information."""
        source_data = {"grant": sample_grant, "asset": sample_asset}
        mock_repo.get_user_sources_with_details.return_value = [source_data]
        mock_repo.count_user_sources.return_value = 1

        result = service.get_user_sources(
            user_id=user_id,
            organization_id=org_id,
            roles=None,
            search=None,
            limit=30,
            offset=0,
        )

        assert len(result.sources) == 1
        assert result.sources[0].id == str(sample_asset.id)
        assert result.sources[0].display_name == sample_asset.display_name
        assert result.sources[0].role == "admin"
        assert result.sources[0].user_id == user_id
        assert result.total == 1


class TestAddUserSources:
    """Tests for add_user_sources method."""

    @patch("app.services.user_service.user_repository")
    def test_adds_user_sources(
        self,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        asset_id: UUID,
        sample_asset: PrimaryAsset,
    ) -> None:
        """Should add user sources successfully."""
        service.session.get.return_value = sample_asset
        mock_user_repo.get_user_source_grant.return_value = None

        request = AddUserSourcesRequest(
            sources=[UserSourceInput(source_id=str(asset_id), role="admin")]
        )

        service.add_user_sources(
            user_id=user_id,
            organization_id=org_id,
            request=request,
        )

        mock_user_repo.create_user_source_grant.assert_called_once()

    def test_raises_404_when_source_not_found(
        self,
        service: UserService,
        user_id: str,
        org_id: str,
        asset_id: UUID,
    ) -> None:
        """Should raise 404 when source not found."""
        service.session.get.return_value = None

        request = AddUserSourcesRequest(
            sources=[UserSourceInput(source_id=str(asset_id), role="admin")]
        )

        with pytest.raises(HTTPException) as exc_info:
            service.add_user_sources(
                user_id=user_id,
                organization_id=org_id,
                request=request,
            )

        assert exc_info.value.status_code == 404

    @patch("app.services.user_service.user_repository")
    def test_raises_409_when_grant_exists(
        self,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        asset_id: UUID,
        sample_asset: PrimaryAsset,
        sample_grant: PrimaryAssetRoleGrant,
    ) -> None:
        """Should raise 409 when user already has access."""
        service.session.get.return_value = sample_asset
        mock_user_repo.get_user_source_grant.return_value = sample_grant

        request = AddUserSourcesRequest(
            sources=[UserSourceInput(source_id=str(asset_id), role="admin")]
        )

        with pytest.raises(HTTPException) as exc_info:
            service.add_user_sources(
                user_id=user_id,
                organization_id=org_id,
                request=request,
            )

        assert exc_info.value.status_code == 409


class TestUpdateUserSources:
    """Tests for update_user_sources method."""

    @patch("app.services.user_service.user_repository")
    def test_updates_user_source_roles(
        self,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        asset_id: UUID,
        sample_asset: PrimaryAsset,
        sample_grant: PrimaryAssetRoleGrant,
    ) -> None:
        """Should update user's source roles successfully."""
        service.session.get.return_value = sample_asset
        mock_user_repo.get_user_source_grant.return_value = sample_grant

        request = UpdateUserSourcesRequest(
            sources=[UserSourceInput(source_id=str(asset_id), role="member")]
        )

        service.update_user_sources(
            user_id=user_id,
            organization_id=org_id,
            request=request,
        )

        assert sample_grant.role == PrimaryAssetRole.asset_member
        service.session.add.assert_called_once_with(sample_grant)
        service.session.commit.assert_called_once()


class TestRemoveUserSources:
    """Tests for remove_user_sources method."""

    @patch("app.services.user_service.user_repository")
    def test_removes_user_sources(
        self,
        mock_user_repo: MagicMock,
        service: UserService,
        user_id: str,
        org_id: str,
        asset_id: UUID,
        sample_asset: PrimaryAsset,
        sample_grant: PrimaryAssetRoleGrant,
    ) -> None:
        """Should remove user sources successfully."""
        service.session.get.return_value = sample_asset
        mock_user_repo.get_user_source_grant.return_value = sample_grant

        request = RemoveUserSourcesRequest(source_ids=[str(asset_id)])

        service.remove_user_sources(
            user_id=user_id,
            organization_id=org_id,
            request=request,
        )

        mock_user_repo.delete_user_source_grant.assert_called_once_with(
            session=service.session,
            grant=sample_grant,
        )
