"""Integration tests for User Profile Service."""

import pytest
from database.models_enums import OrgRole, PrimaryAssetRole, PrincipalKind, TeamRole
from sqlmodel import Session

from app.auth.models import User
from app.services.user_profile_service import UserProfileService
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
class TestUserProfileIntegration:
    """Integration tests for User Profile operations."""

    def test_get_current_user_profile_basic(
        self, integration_db_session: Session
    ) -> None:
        """Test getting current user profile with basic user."""
        # Create a basic user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|test123",
            email="test@example.com",
            name="Test User",
            organization_id="test-org-id",
            org_role=OrgRole.member,
        )

        # Create mock JWT user
        mock_user = create_mock_user(db_user.id, "test-org-id")

        # Get profile
        service = UserProfileService(integration_db_session)
        profile = service.get_current_user_profile(mock_user)

        # Assertions
        assert profile.id == db_user.id
        assert profile.email == "test@example.com"
        assert profile.name == "Test User"
        assert profile.organization_id == "test-org-id"
        assert profile.org_role == "member"
        assert profile.entitlements is None
        assert profile.team_admin is False
        assert profile.source_admin is False

    def test_get_current_user_profile_with_team_admin(
        self, integration_db_session: Session
    ) -> None:
        """Test getting profile for user who is team admin."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|test456",
            email="admin@example.com",
            name="Admin User",
            organization_id="test-org-id",
            org_role=OrgRole.member,
        )

        # Create team and make user an admin
        team = TeamFactory.create(
            session=integration_db_session,
            name="Test Team",
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=team.id,
            user_id=db_user.id,
            role=TeamRole.team_admin,
            organization_id="test-org-id",
        )

        # Create mock JWT user
        mock_user = create_mock_user(db_user.id, "test-org-id")

        # Get profile
        service = UserProfileService(integration_db_session)
        profile = service.get_current_user_profile(mock_user)

        # Assertions
        assert profile.team_admin is True
        assert profile.source_admin is False

    def test_get_current_user_profile_with_source_admin(
        self, integration_db_session: Session
    ) -> None:
        """Test getting profile for user who has source admin role."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|test789",
            email="sourceadmin@example.com",
            name="Source Admin User",
            organization_id="test-org-id",
            org_role=OrgRole.member,
        )

        # Create source
        source = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Test Source",
            organization_id="test-org-id",
        )

        # Grant user admin access to source
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.admin,
            user_id=db_user.id,
            organization_id="test-org-id",
        )

        # Create mock JWT user
        mock_user = create_mock_user(db_user.id, "test-org-id")

        # Get profile
        service = UserProfileService(integration_db_session)
        profile = service.get_current_user_profile(mock_user)

        # Assertions
        assert profile.team_admin is False
        assert profile.source_admin is True

    def test_get_current_user_profile_super_admin(
        self, integration_db_session: Session
    ) -> None:
        """Test getting profile for super admin user."""
        # Create super admin user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|superadmin",
            email="superadmin@example.com",
            name="Super Admin",
            organization_id="test-org-id",
            org_role=OrgRole.super_admin,
        )

        # Create mock JWT user
        mock_user = create_mock_user(db_user.id, "test-org-id")

        # Get profile
        service = UserProfileService(integration_db_session)
        profile = service.get_current_user_profile(mock_user)

        # Assertions
        assert profile.org_role == "super_admin"
        assert profile.team_admin is False
        assert profile.source_admin is False

    def test_get_current_user_profile_with_all_roles(
        self, integration_db_session: Session
    ) -> None:
        """Test getting profile for user with both team_admin and source_admin."""
        # Create user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|allroles",
            email="allroles@example.com",
            name="All Roles User",
            organization_id="test-org-id",
            org_role=OrgRole.super_admin,
        )

        # Create team and make user an admin
        team = TeamFactory.create(
            session=integration_db_session,
            name="Test Team",
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=team.id,
            user_id=db_user.id,
            role=TeamRole.team_admin,
            organization_id="test-org-id",
        )

        # Create source and grant admin access
        source = PrimaryAssetFactory.create(
            session=integration_db_session,
            display_name="Test Source",
            organization_id="test-org-id",
        )
        PrimaryAssetRoleGrantFactory.create(
            session=integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.user,
            role=PrimaryAssetRole.admin,
            user_id=db_user.id,
            organization_id="test-org-id",
        )

        # Create mock JWT user
        mock_user = create_mock_user(db_user.id, "test-org-id")

        # Get profile
        service = UserProfileService(integration_db_session)
        profile = service.get_current_user_profile(mock_user)

        # Assertions
        assert profile.org_role == "super_admin"
        assert profile.team_admin is True
        assert profile.source_admin is True
