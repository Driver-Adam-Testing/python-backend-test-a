"""Integration tests for User Sources endpoint."""

import pytest
from database.models_enums import OrgRole, PrimaryAssetRole, PrincipalKind, TeamRole
from sqlmodel import Session

from app.auth.models import User
from app.schemas.user_schema import AssignmentType
from app.services.user_service import UserService
from app.test_factories import (
    Auth0UserFactory,
    PrimaryAssetFactory,
    PrimaryAssetRoleGrantFactory,
    TeamFactory,
    TeamMembershipFactory,
)


def create_mock_user(user_id: str, organization_id: str) -> User:
    """Create a mock User from JWT token."""
    return User.model_validate(
        {
            "sub": user_id,
            "org_id": organization_id,
            "org_name": "Test Org",
            "iss": "https://test.auth0.com/",
            "aud": ["api"],
            "iat": 1234567890,
            "exp": 9999999999,
            "scope": "",
            "azp": "test",
            "permissions": [],
            "user_email": "test@example.com",
            "user_full_name": "Test User",
        }
    )


@pytest.mark.integration
class TestUserSourcesIntegration:
    """Integration tests for user sources operations."""

    def test_get_user_sources_with_direct_grant(
        self, integration_db_session: Session
    ) -> None:
        """Test getting user sources with direct user grant."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|test123",
            email="test@example.com",
            name="Test User",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create asset
        asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Test Codebase",
            organization_id="test-org-id",
        )

        # Create direct user grant
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.user,
            user_id=db_user.id,
            role=PrimaryAssetRole.asset_member,
        )

        # Get sources
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_sources(
            user=mock_user,
            user_id=db_user.id,
        )

        # Assertions
        assert result.total == 1
        assert len(result.sources) == 1
        source = result.sources[0]
        assert source.display_name == "Test Codebase"
        assert source.effective_role == PrimaryAssetRole.asset_member
        assert source.source_role == PrimaryAssetRole.asset_member
        assert source.asset_org_role is None
        assert source.user_org_role == OrgRole.org_member
        assert source.is_super_admin is False
        assert source.assignment_type == AssignmentType.DIRECT
        assert len(source.teams) == 0

    def test_get_user_sources_with_org_grant(
        self, integration_db_session: Session
    ) -> None:
        """Test getting user sources with org-wide grant."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|test456",
            email="test@example.com",
            name="Test User",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create asset
        asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Org Shared Codebase",
            organization_id="test-org-id",
        )

        # Create org-wide grant
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
        )

        # Get sources
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_sources(
            user=mock_user,
            user_id=db_user.id,
        )

        # Assertions
        assert result.total == 1
        source = result.sources[0]
        assert source.display_name == "Org Shared Codebase"
        assert source.effective_role == PrimaryAssetRole.asset_member
        assert source.source_role is None
        assert source.asset_org_role == PrimaryAssetRole.asset_member
        assert source.assignment_type == AssignmentType.INHERITED

    def test_get_user_sources_with_team_grant(
        self, integration_db_session: Session
    ) -> None:
        """Test getting user sources with team grant."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|test789",
            email="test@example.com",
            name="Test User",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create team
        team = TeamFactory.create(
            session=integration_db_session,
            name="Engineering Team",
            organization_id="test-org-id",
        )

        # Add user to team
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=team.id,
            user_id=db_user.id,
            role=TeamRole.team_member,
            organization_id="test-org-id",
        )

        # Create asset
        asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Team Codebase",
            organization_id="test-org-id",
        )

        # Create team grant
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.team,
            team_id=team.id,
            role=PrimaryAssetRole.asset_admin,
        )

        # Get sources
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_sources(
            user=mock_user,
            user_id=db_user.id,
        )

        # Assertions
        assert result.total == 1
        source = result.sources[0]
        assert source.display_name == "Team Codebase"
        assert source.effective_role == PrimaryAssetRole.asset_admin
        assert source.source_role is None
        assert source.assignment_type == AssignmentType.INHERITED
        assert len(source.teams) == 1
        team_info = source.teams[0]
        assert team_info.display_name == "Engineering Team"
        assert team_info.team_role == TeamRole.team_member
        assert team_info.source_role == PrimaryAssetRole.asset_admin

    def test_get_user_sources_with_super_admin(
        self, integration_db_session: Session
    ) -> None:
        """Test getting user sources as super admin."""
        # Create super admin user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|admin123",
            email="admin@example.com",
            name="Admin User",
            organization_id="test-org-id",
            org_role=OrgRole.org_super_admin,
        )

        # Create asset (no explicit grant needed for super admin)
        asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Private Codebase",
            organization_id="test-org-id",
        )

        # Create a grant for someone else so asset exists in DB
        other_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|other",
            organization_id="test-org-id",
        )
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.user,
            user_id=other_user.id,
            role=PrimaryAssetRole.asset_member,
        )

        # Get sources as super admin
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_sources(
            user=mock_user,
            user_id=db_user.id,
        )

        # Super admin sees all assets in org
        assert result.total == 1
        source = result.sources[0]
        assert source.effective_role == PrimaryAssetRole.asset_admin
        assert source.is_super_admin is True
        assert source.user_org_role == OrgRole.org_super_admin
        assert source.assignment_type == AssignmentType.INHERITED

    def test_filter_by_assignment_type_direct(
        self, integration_db_session: Session
    ) -> None:
        """Test filtering sources by assignment_type=direct."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|filter123",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create asset with direct grant
        direct_asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Direct Access",
            organization_id="test-org-id",
        )
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=direct_asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.user,
            user_id=db_user.id,
            role=PrimaryAssetRole.asset_member,
        )

        # Create asset with org grant (inherited)
        org_asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Org Access",
            organization_id="test-org-id",
        )
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=org_asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
        )

        # Get sources with direct filter
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_sources(
            user=mock_user,
            user_id=db_user.id,
            assignment_type=AssignmentType.DIRECT,
        )

        # Should only see direct grant
        assert result.total == 1
        assert result.sources[0].display_name == "Direct Access"
        assert result.sources[0].assignment_type == AssignmentType.DIRECT

    def test_filter_by_assignment_type_inherited(
        self, integration_db_session: Session
    ) -> None:
        """Test filtering sources by assignment_type=inherited."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|filter456",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create asset with direct grant
        direct_asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Direct Access",
            organization_id="test-org-id",
        )
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=direct_asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.user,
            user_id=db_user.id,
            role=PrimaryAssetRole.asset_member,
        )

        # Create asset with org grant (inherited)
        org_asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Org Access",
            organization_id="test-org-id",
        )
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=org_asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
        )

        # Get sources with inherited filter
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_sources(
            user=mock_user,
            user_id=db_user.id,
            assignment_type=AssignmentType.INHERITED,
        )

        # Should only see inherited grant
        assert result.total == 1
        assert result.sources[0].display_name == "Org Access"
        assert result.sources[0].assignment_type == AssignmentType.INHERITED

    def test_multiple_teams_on_same_asset(
        self, integration_db_session: Session
    ) -> None:
        """Test user has access via multiple teams to same asset."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|multiteam",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create two teams
        team1 = TeamFactory.create(
            session=integration_db_session,
            name="Frontend Team",
            organization_id="test-org-id",
        )
        team2 = TeamFactory.create(
            session=integration_db_session,
            name="Backend Team",
            organization_id="test-org-id",
        )

        # Add user to both teams with different roles
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=team1.id,
            user_id=db_user.id,
            role=TeamRole.team_admin,
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=team2.id,
            user_id=db_user.id,
            role=TeamRole.team_member,
            organization_id="test-org-id",
        )

        # Create asset
        asset = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Shared Codebase",
            organization_id="test-org-id",
        )

        # Both teams have grants with different roles
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.team,
            team_id=team1.id,
            role=PrimaryAssetRole.asset_member,
        )
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=asset.id,
            organization_id="test-org-id",
            principal_kind=PrincipalKind.team,
            team_id=team2.id,
            role=PrimaryAssetRole.asset_admin,
        )

        # Get sources
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_sources(
            user=mock_user,
            user_id=db_user.id,
        )

        # Should see both teams
        assert result.total == 1
        source = result.sources[0]
        assert source.effective_role == PrimaryAssetRole.asset_admin  # Highest
        assert len(source.teams) == 2

        # Teams should be sorted by name
        assert source.teams[0].display_name == "Backend Team"
        assert source.teams[0].team_role == TeamRole.team_member
        assert source.teams[0].source_role == PrimaryAssetRole.asset_admin

        assert source.teams[1].display_name == "Frontend Team"
        assert source.teams[1].team_role == TeamRole.team_admin
        assert source.teams[1].source_role == PrimaryAssetRole.asset_member
