"""Integration tests for User Teams endpoint."""

import pytest
from database.models_enums import OrgRole, TeamRole
from sqlmodel import Session

from app.auth.models import User
from app.services.user_service import UserService
from app.test_factories import (
    Auth0UserFactory,
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
class TestUserTeamsIntegration:
    """Integration tests for user teams operations."""

    def test_filter_by_roles_team_admin(self, integration_db_session: Session) -> None:
        """Test filtering teams by roles=[team_admin]."""
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|teamfilter1",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create team where user is admin
        admin_team = TeamFactory.create(
            session=integration_db_session,
            name="Admin Team",
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=admin_team.id,
            user_id=db_user.id,
            role=TeamRole.team_admin,
            organization_id="test-org-id",
        )

        # Create team where user is member
        member_team = TeamFactory.create(
            session=integration_db_session,
            name="Member Team",
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=member_team.id,
            user_id=db_user.id,
            role=TeamRole.team_member,
            organization_id="test-org-id",
        )

        # Filter by team_admin role
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_teams(
            user=mock_user,
            user_id=db_user.id,
            roles=[TeamRole.team_admin],
        )

        # Should only see admin team
        assert result.total == 1
        assert result.teams[0].name == "Admin Team"
        assert result.teams[0].role == TeamRole.team_admin

    def test_filter_by_roles_team_member(self, integration_db_session: Session) -> None:
        """Test filtering teams by roles=[team_member]."""
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|teamfilter2",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create team where user is admin
        admin_team = TeamFactory.create(
            session=integration_db_session,
            name="Admin Team",
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=admin_team.id,
            user_id=db_user.id,
            role=TeamRole.team_admin,
            organization_id="test-org-id",
        )

        # Create team where user is member
        member_team = TeamFactory.create(
            session=integration_db_session,
            name="Member Team",
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=member_team.id,
            user_id=db_user.id,
            role=TeamRole.team_member,
            organization_id="test-org-id",
        )

        # Filter by team_member role
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_teams(
            user=mock_user,
            user_id=db_user.id,
            roles=[TeamRole.team_member],
        )

        # Should only see member team
        assert result.total == 1
        assert result.teams[0].name == "Member Team"
        assert result.teams[0].role == TeamRole.team_member

    def test_filter_by_multiple_team_roles(
        self, integration_db_session: Session
    ) -> None:
        """Test filtering teams by multiple roles."""
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="auth0|teamfilter3",
            organization_id="test-org-id",
            org_role=OrgRole.org_member,
        )

        # Create team where user is admin
        admin_team = TeamFactory.create(
            session=integration_db_session,
            name="Admin Team",
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=admin_team.id,
            user_id=db_user.id,
            role=TeamRole.team_admin,
            organization_id="test-org-id",
        )

        # Create team where user is member
        member_team = TeamFactory.create(
            session=integration_db_session,
            name="Member Team",
            organization_id="test-org-id",
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=member_team.id,
            user_id=db_user.id,
            role=TeamRole.team_member,
            organization_id="test-org-id",
        )

        # Filter by both roles
        mock_user = create_mock_user(db_user.id, "test-org-id")
        service = UserService(integration_db_session)
        result = service.get_user_teams(
            user=mock_user,
            user_id=db_user.id,
            roles=[TeamRole.team_admin, TeamRole.team_member],
        )

        # Should see both teams
        assert result.total == 2
        team_names = {t.name for t in result.teams}
        assert team_names == {"Admin Team", "Member Team"}
