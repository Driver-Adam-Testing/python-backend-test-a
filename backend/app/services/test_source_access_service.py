"""Unit tests for SourceAccessService business logic."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from database.models import PrimaryAsset, PrimaryAssetRoleGrant, Team, User
from database.models_enums import (
    PrimaryAssetKind,
    PrimaryAssetProvider,
    PrimaryAssetRole,
    PrincipalKind,
)
from fastapi import HTTPException

from app.schemas.source_access_schema import (
    AddSourceMembersRequest,
    AddTeamSourcesRequest,
    RemoveSourceMembersRequest,
    RemoveTeamSourcesRequest,
    SourceMemberInput,
    TeamSourceInput,
    UpdateSourceMembersRequest,
    UpdateTeamSourcesRequest,
)
from app.services.source_access_service import (
    SourceAccessService,
    grant_to_source_member_response,
    grant_to_team_source_response,
    map_source_role_to_backend,
    map_source_role_to_frontend,
)


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def service(session: MagicMock) -> SourceAccessService:
    """Create a SourceAccessService instance."""
    return SourceAccessService(session)


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
    asset.created_at = datetime.now()
    asset.updated_at = datetime.now()
    return asset


@pytest.fixture
def sample_grant(team_id: UUID, asset_id: UUID, org_id: str) -> PrimaryAssetRoleGrant:
    """Create a sample grant."""
    grant = PrimaryAssetRoleGrant(
        id=uuid4(),
        primary_asset_id=asset_id,
        organization_id=org_id,
        principal_kind=PrincipalKind.team,
        team_id=team_id,
        user_id=None,
        role=PrimaryAssetRole.admin,
    )
    grant.created_at = datetime.now()
    return grant


class TestRoleMappingFunctions:
    """Tests for role mapping utility functions."""

    def test_map_source_role_to_backend_admin(self) -> None:
        """Should map 'admin' to PrimaryAssetRole.admin."""
        result = map_source_role_to_backend("admin")
        assert result == PrimaryAssetRole.admin

    def test_map_source_role_to_backend_member(self) -> None:
        """Should map 'member' to PrimaryAssetRole.viewer."""
        result = map_source_role_to_backend("member")
        assert result == PrimaryAssetRole.viewer

    def test_map_source_role_to_backend_invalid_raises_error(self) -> None:
        """Should raise ValueError for invalid role."""
        with pytest.raises(ValueError, match="Invalid role"):
            map_source_role_to_backend("invalid")

    def test_map_source_role_to_frontend_admin(self) -> None:
        """Should map PrimaryAssetRole.admin to 'admin'."""
        result = map_source_role_to_frontend(PrimaryAssetRole.admin)
        assert result == "admin"

    def test_map_source_role_to_frontend_viewer(self) -> None:
        """Should map PrimaryAssetRole.viewer to 'member'."""
        result = map_source_role_to_frontend(PrimaryAssetRole.viewer)
        assert result == "member"


class TestGrantToTeamSourceResponse:
    """Tests for grant_to_team_source_response function."""

    def test_converts_grant_and_asset_to_response(
        self, sample_grant: PrimaryAssetRoleGrant, sample_asset: PrimaryAsset
    ) -> None:
        """Should convert grant and asset to TeamSourceResponse."""
        response = grant_to_team_source_response(sample_grant, sample_asset)

        assert response.id == str(sample_asset.id)
        assert response.display_name == "Test Codebase"
        assert response.kind == "CODEBASE"
        assert response.role == "admin"
        assert response.visibility == "private"


class TestGrantToSourceMemberResponse:
    """Tests for grant_to_source_member_response function."""

    def test_converts_user_member(
        self,
        sample_grant: PrimaryAssetRoleGrant,
        sample_asset: PrimaryAsset,
        sample_user: User,
    ) -> None:
        """Should convert user member to SourceMemberResponse."""
        response = grant_to_source_member_response(
            sample_grant, sample_asset, sample_user, "user"
        )

        assert response.member_id == sample_user.id
        assert response.kind == "user"
        assert response.name == "John Doe"
        assert response.email == "john@example.com"

    def test_converts_team_member(
        self,
        sample_grant: PrimaryAssetRoleGrant,
        sample_asset: PrimaryAsset,
        sample_team: Team,
    ) -> None:
        """Should convert team member to SourceMemberResponse."""
        response = grant_to_source_member_response(
            sample_grant, sample_asset, sample_team, "team"
        )

        assert response.member_id == str(sample_team.id)
        assert response.kind == "team"
        assert response.name == "Engineering"
        assert response.email is None
        assert response.picture is None


class TestGetTeamSources:
    """Tests for get_team_sources method."""

    @patch("app.services.source_access_service.team_repository")
    @patch("app.services.source_access_service.acl_repository")
    def test_returns_team_sources(
        self,
        mock_acl_repo: MagicMock,
        mock_team_repo: MagicMock,
        service: SourceAccessService,
        sample_team: Team,
        sample_grant: PrimaryAssetRoleGrant,
        sample_asset: PrimaryAsset,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should return team sources with filtering."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_acl_repo.get_team_sources_with_details.return_value = [
            {"grant": sample_grant, "asset": sample_asset}
        ]
        mock_acl_repo.count_team_sources.return_value = 1

        response = service.get_team_sources(
            team_id=team_id,
            organization_id=org_id,
            limit=30,
            offset=0,
        )

        assert response.total == 1
        assert len(response.sources) == 1
        assert response.sources[0].display_name == "Test Codebase"

    @patch("app.services.source_access_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_team_repo: MagicMock,
        service: SourceAccessService,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise 404 when team does not exist."""
        mock_team_repo.get_team_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.get_team_sources(
                team_id=team_id,
                organization_id=org_id,
            )

        assert exc_info.value.status_code == 404


class TestAddTeamSources:
    """Tests for add_team_sources method."""

    @patch("app.services.source_access_service.team_repository")
    @patch("app.services.source_access_service.acl_repository")
    def test_adds_sources_to_team(
        self,
        mock_acl_repo: MagicMock,
        mock_team_repo: MagicMock,
        service: SourceAccessService,
        sample_team: Team,
        sample_asset: PrimaryAsset,
        team_id: UUID,
        asset_id: UUID,
        org_id: str,
        session: MagicMock,
    ) -> None:
        """Should add sources to team successfully."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_acl_repo.get_primary_asset_by_id.return_value = sample_asset

        request = AddTeamSourcesRequest(
            sources=[TeamSourceInput(source_id=str(asset_id), role="admin")]
        )

        service.add_team_sources(
            team_id=team_id,
            organization_id=org_id,
            request=request,
        )

        session.add.assert_called()
        session.commit.assert_called_once()

    @patch("app.services.source_access_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_team_repo: MagicMock,
        service: SourceAccessService,
        team_id: UUID,
        asset_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise 404 when team does not exist."""
        mock_team_repo.get_team_by_id.return_value = None

        request = AddTeamSourcesRequest(
            sources=[TeamSourceInput(source_id=str(asset_id), role="admin")]
        )

        with pytest.raises(HTTPException) as exc_info:
            service.add_team_sources(
                team_id=team_id,
                organization_id=org_id,
                request=request,
            )

        assert exc_info.value.status_code == 404


class TestUpdateTeamSources:
    """Tests for update_team_sources method."""

    @patch("app.services.source_access_service.team_repository")
    @patch("app.services.source_access_service.acl_repository")
    def test_updates_source_roles(
        self,
        mock_acl_repo: MagicMock,
        mock_team_repo: MagicMock,
        service: SourceAccessService,
        sample_team: Team,
        sample_grant: PrimaryAssetRoleGrant,
        team_id: UUID,
        asset_id: UUID,
        org_id: str,
        session: MagicMock,
    ) -> None:
        """Should update source roles successfully."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_acl_repo.get_grant_by_team_and_asset.return_value = sample_grant

        request = UpdateTeamSourcesRequest(
            sources=[TeamSourceInput(source_id=str(asset_id), role="member")]
        )

        service.update_team_sources(
            team_id=team_id,
            organization_id=org_id,
            request=request,
        )

        assert sample_grant.role == PrimaryAssetRole.viewer
        session.add.assert_called()
        session.commit.assert_called_once()


class TestRemoveTeamSources:
    """Tests for remove_team_sources method."""

    @patch("app.services.source_access_service.team_repository")
    @patch("app.services.source_access_service.acl_repository")
    def test_removes_sources_from_team(
        self,
        mock_acl_repo: MagicMock,
        mock_team_repo: MagicMock,
        service: SourceAccessService,
        sample_team: Team,
        sample_grant: PrimaryAssetRoleGrant,
        team_id: UUID,
        asset_id: UUID,
        org_id: str,
        session: MagicMock,
    ) -> None:
        """Should remove sources from team successfully."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_acl_repo.get_grant_by_team_and_asset.return_value = sample_grant

        request = RemoveTeamSourcesRequest(source_ids=[str(asset_id)])

        service.remove_team_sources(
            team_id=team_id,
            organization_id=org_id,
            request=request,
        )

        session.delete.assert_called()
        session.commit.assert_called_once()


class TestGetSourceMembers:
    """Tests for get_source_members method."""

    @patch("app.services.source_access_service.acl_repository")
    def test_returns_source_members(
        self,
        mock_acl_repo: MagicMock,
        service: SourceAccessService,
        sample_asset: PrimaryAsset,
        sample_grant: PrimaryAssetRoleGrant,
        sample_user: User,
        asset_id: UUID,
        org_id: str,
    ) -> None:
        """Should return source members with details."""
        mock_acl_repo.get_primary_asset_by_id.return_value = sample_asset
        mock_acl_repo.get_source_members_with_details.return_value = [
            {
                "grant": sample_grant,
                "asset": sample_asset,
                "member": sample_user,
                "kind": "user",
            }
        ]
        mock_acl_repo.count_source_members.return_value = 1

        response = service.get_source_members(
            source_id=asset_id,
            organization_id=org_id,
            limit=30,
            offset=0,
        )

        assert response.total == 1
        assert len(response.members) == 1

    @patch("app.services.source_access_service.acl_repository")
    def test_raises_404_when_source_not_found(
        self,
        mock_acl_repo: MagicMock,
        service: SourceAccessService,
        asset_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise 404 when source does not exist."""
        mock_acl_repo.get_primary_asset_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.get_source_members(
                source_id=asset_id,
                organization_id=org_id,
            )

        assert exc_info.value.status_code == 404


class TestAddSourceMembers:
    """Tests for add_source_members method."""

    @patch("app.services.source_access_service.acl_repository")
    def test_adds_members_to_source(
        self,
        mock_acl_repo: MagicMock,
        service: SourceAccessService,
        sample_asset: PrimaryAsset,
        asset_id: UUID,
        user_id: str,
        org_id: str,
        session: MagicMock,
    ) -> None:
        """Should add members to source successfully."""
        mock_acl_repo.get_primary_asset_by_id.return_value = sample_asset

        request = AddSourceMembersRequest(
            members=[SourceMemberInput(member_id=user_id, kind="user", role="admin")]
        )

        service.add_source_members(
            source_id=asset_id,
            organization_id=org_id,
            request=request,
        )

        session.add.assert_called()
        session.commit.assert_called_once()


class TestUpdateSourceMembers:
    """Tests for update_source_members method."""

    @patch("app.services.source_access_service.acl_repository")
    def test_updates_member_roles(
        self,
        mock_acl_repo: MagicMock,
        service: SourceAccessService,
        sample_asset: PrimaryAsset,
        sample_grant: PrimaryAssetRoleGrant,
        asset_id: UUID,
        user_id: str,
        org_id: str,
        session: MagicMock,
    ) -> None:
        """Should update member roles successfully."""
        mock_acl_repo.get_primary_asset_by_id.return_value = sample_asset
        mock_acl_repo.get_grant_by_user_and_asset.return_value = sample_grant

        request = UpdateSourceMembersRequest(
            members=[SourceMemberInput(member_id=user_id, kind="user", role="member")]
        )

        service.update_source_members(
            source_id=asset_id,
            organization_id=org_id,
            request=request,
        )

        session.add.assert_called()
        session.commit.assert_called_once()


class TestRemoveSourceMembers:
    """Tests for remove_source_members method."""

    @patch("app.services.source_access_service.acl_repository")
    def test_removes_members_from_source(
        self,
        mock_acl_repo: MagicMock,
        service: SourceAccessService,
        sample_asset: PrimaryAsset,
        sample_grant: PrimaryAssetRoleGrant,
        asset_id: UUID,
        user_id: str,
        org_id: str,
        session: MagicMock,
    ) -> None:
        """Should remove members from source successfully."""
        mock_acl_repo.get_primary_asset_by_id.return_value = sample_asset
        mock_acl_repo.get_grant_by_user_and_asset.return_value = sample_grant

        request = RemoveSourceMembersRequest(
            members=[{"member_id": user_id, "kind": "user"}]
        )

        service.remove_source_members(
            source_id=asset_id,
            organization_id=org_id,
            request=request,
        )

        session.delete.assert_called()
        session.commit.assert_called_once()
