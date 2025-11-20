"""
Integration tests for TeamService.

These tests use a real in-memory database to verify end-to-end workflows.
They are marked with @pytest.mark.integration and should be run separately from unit tests.

Run with: pytest -m integration
"""

import pytest
from database.models import Team, TeamMembership
from database.models import User as DbUser
from database.models_enums import OrgRole, TeamRole
from sqlmodel import Session, select

from app.auth.models import User
from app.schemas.team_member_schema import (
    AddTeamMembersRequest,
    RemoveTeamMembersRequest,
    TeamMemberAddInput,
    UpdateTeamMembersRequest,
)
from app.schemas.team_schema import (
    CreateTeamRequest,
    TeamMemberInput,
    UpdateTeamRequest,
)
from app.services.team_member_service import TeamMemberService
from app.services.team_service import TeamService
from app.test_factories import Auth0UserFactory, TeamFactory, TeamMembershipFactory


def create_mock_user(organization_id: str, user_id: str = "test-user-id") -> User:
    """Create a mock User object for testing."""
    return User(
        org_id=organization_id,
        org_name="Test Organization",
        sub=user_id,
        iss="https://test.auth0.com/",
        aud=["test-audience"],
        iat=1234567890,
        exp=9999999999,
        scope="",
        azp="",
        permissions=[],
        user_email="test@example.com",
        user_full_name="Test User",
    )


@pytest.mark.integration
class TestTeamLifecycleIntegration:
    """Test complete team lifecycle: Create → Add members → Update → Remove → Delete."""

    def test_complete_team_lifecycle_e2e(self, integration_db_session: Session) -> None:
        """
        Test full team lifecycle workflow.

        Steps:
        1. Create team with 2 initial members (1 admin, 1 member)
        2. Verify team and memberships exist in DB
        3. Add 3 more members
        4. Update 1 member's role from member to admin
        5. Remove 2 members
        6. Delete team
        7. Verify all data cleaned up
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)

        # Ensure mock_user exists in DB as super admin so they can access teams
        Auth0UserFactory.create(
            integration_db_session,
            user_id=mock_user.user_id,
            organization_id=org_id,
            org_role=OrgRole.org_super_admin,
            email="test-user@example.com",
            name="Test User",
        )

        service = TeamService(integration_db_session)
        member_service = TeamMemberService(integration_db_session)

        # Create test users
        user1 = Auth0UserFactory.create(
            integration_db_session, name="Alice", organization_id=org_id
        )
        user2 = Auth0UserFactory.create(
            integration_db_session, name="Bob", organization_id=org_id
        )
        user3 = Auth0UserFactory.create(
            integration_db_session, name="Charlie", organization_id=org_id
        )
        user4 = Auth0UserFactory.create(
            integration_db_session, name="Diana", organization_id=org_id
        )
        user5 = Auth0UserFactory.create(
            integration_db_session, name="Eve", organization_id=org_id
        )

        # Step 1: Create team with 2 initial members
        create_request = CreateTeamRequest(
            name="Engineering",
            members=[
                TeamMemberInput(user_id=user1.id, role="team_admin"),
                TeamMemberInput(user_id=user2.id, role="team_member"),
            ],
        )
        team_response = service.create_team(user=mock_user, request=create_request)

        # Step 2: Verify team exists in DB
        team_in_db = integration_db_session.get(Team, team_response.id)
        assert team_in_db is not None
        assert team_in_db.name == "Engineering"
        assert team_response.admins == 1
        assert team_response.members == 1

        # Verify memberships exist
        memberships = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.team_id == team_in_db.id)
        ).all()
        assert len(memberships) == 2
        admin_count = sum(1 for m in memberships if m.role == TeamRole.team_admin)
        member_count = sum(1 for m in memberships if m.role == TeamRole.team_member)
        assert admin_count == 1
        assert member_count == 1

        # Step 3: Add 3 more members
        member_service.add_team_members(
            user=mock_user,
            team_id=team_in_db.id,
            request=AddTeamMembersRequest(
                members=[
                    TeamMemberAddInput(user_id=user3.id, role="team_member"),
                    TeamMemberAddInput(user_id=user4.id, role="team_member"),
                    TeamMemberAddInput(user_id=user5.id, role="team_admin"),
                ]
            ),
        )

        # Verify counts updated
        memberships_after_add = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.team_id == team_in_db.id)
        ).all()
        assert len(memberships_after_add) == 5

        # Get team to verify aggregated counts
        team_after_add = service.get_team(user=mock_user, team_id=team_in_db.id)
        assert team_after_add.admins == 2  # Alice + Eve
        assert team_after_add.members == 3  # Bob + Charlie + Diana

        # Step 4: Update Bob's role from member to admin
        member_service.update_team_members(
            user=mock_user,
            team_id=team_in_db.id,
            request=UpdateTeamMembersRequest(
                members=[TeamMemberAddInput(user_id=user2.id, role="team_admin")]
            ),
        )

        # Verify role updated in DB
        bob_membership = integration_db_session.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == team_in_db.id,
                TeamMembership.user_id == user2.id,
            )
        ).first()
        assert bob_membership.role == TeamRole.team_admin

        # Verify counts updated
        team_after_update = service.get_team(user=mock_user, team_id=team_in_db.id)
        assert team_after_update.admins == 3  # Alice + Bob + Eve
        assert team_after_update.members == 2  # Charlie + Diana

        # Step 5: Remove 2 members (Charlie and Diana)
        member_service.remove_team_members(
            user=mock_user,
            team_id=team_in_db.id,
            request=RemoveTeamMembersRequest(user_ids=[user3.id, user4.id]),
        )

        # Verify members removed
        memberships_after_remove = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.team_id == team_in_db.id)
        ).all()
        assert len(memberships_after_remove) == 3  # Alice, Bob, Eve remain

        # Verify counts updated
        team_after_remove = service.get_team(user=mock_user, team_id=team_in_db.id)
        assert team_after_remove.admins == 3  # Alice + Bob + Eve
        assert team_after_remove.members == 0  # All members are now admins

        # Step 6: Delete team
        service.delete_team(user=mock_user, team_id=team_in_db.id)

        # Step 7: Verify team deleted from DB
        team_deleted = integration_db_session.get(Team, team_in_db.id)
        assert team_deleted is None

        # Verify all memberships deleted (cascading delete)
        memberships_after_delete = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.team_id == team_in_db.id)
        ).all()
        assert len(memberships_after_delete) == 0

        # Verify users still exist (not deleted)
        user1_still_exists = integration_db_session.exec(
            select(DbUser).where(DbUser.id == user1.id)
        ).first()
        assert user1_still_exists is not None

    def test_create_team_without_members(self, integration_db_session: Session) -> None:
        """Test creating a team with no initial members."""
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = TeamService(integration_db_session)

        create_request = CreateTeamRequest(name="Empty Team", members=None)
        team_response = service.create_team(user=mock_user, request=create_request)

        # Verify team created
        assert team_response.name == "Empty Team"
        assert team_response.admins == 0
        assert team_response.members == 0

        # Verify no memberships
        from uuid import UUID

        memberships = integration_db_session.exec(
            select(TeamMembership).where(
                TeamMembership.team_id == UUID(team_response.id)
            )
        ).all()
        assert len(memberships) == 0

    def test_update_team_name(self, integration_db_session: Session) -> None:
        """Test updating a team's name."""
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = TeamService(integration_db_session)

        # Create team
        team = TeamFactory.create(
            integration_db_session, name="Old Name", organization_id=org_id
        )

        # Update name
        update_request = UpdateTeamRequest(name="New Name")
        updated_team = service.update_team(
            user=mock_user, team_id=team.id, request=update_request
        )

        # Verify name updated
        assert updated_team.name == "New Name"

        # Verify in DB
        team_in_db = integration_db_session.get(Team, team.id)
        assert team_in_db.name == "New Name"


@pytest.mark.integration
class TestTeamPaginationIntegration:
    """Test team pagination with real data."""

    def test_get_teams_pagination_with_search_as_super_admin(
        self, integration_db_session: Session
    ) -> None:
        """Test pagination and search with multiple teams as super admin."""
        org_id = "test-org-id"

        # Create super admin user
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="test-super-admin",
            email="admin@example.com",
            name="Super Admin",
            organization_id=org_id,
            org_role=OrgRole.org_super_admin,
        )
        mock_user = create_mock_user(org_id, db_user.id)
        service = TeamService(integration_db_session)

        # Create 15 teams
        for i in range(15):
            TeamFactory.create(
                integration_db_session,
                name=f"Team {i:02d}",
                organization_id=org_id,
            )

        # Create 5 teams with "Engineering" in the name
        for i in range(5):
            TeamFactory.create(
                integration_db_session,
                name=f"Engineering {i}",
                organization_id=org_id,
            )

        # Test 1: Get all teams (first page) - super admin sees all
        all_teams_page1 = service.get_teams(user=mock_user, limit=10, offset=0)
        assert len(all_teams_page1.teams) == 10
        assert all_teams_page1.total == 20

        # Test 2: Get second page
        all_teams_page2 = service.get_teams(user=mock_user, limit=10, offset=10)
        assert len(all_teams_page2.teams) == 10
        assert all_teams_page2.total == 20

        # Test 3: Search for "Engineering"
        eng_teams = service.get_teams(
            user=mock_user, search="Engineering", limit=30, offset=0
        )
        assert len(eng_teams.teams) == 5
        assert eng_teams.total == 5
        assert all("Engineering" in team.name for team in eng_teams.teams)

        # Test 4: Search with pagination
        eng_teams_page1 = service.get_teams(
            user=mock_user, search="Engineering", limit=2, offset=0
        )
        assert len(eng_teams_page1.teams) == 2
        assert eng_teams_page1.total == 5

    def test_get_teams_as_regular_user_only_shows_member_teams(
        self, integration_db_session: Session
    ) -> None:
        """Test that regular users only see teams they are members of."""
        org_id = "test-org-id"

        # Create regular user (not super admin)
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="test-regular-user",
            email="user@example.com",
            name="Regular User",
            organization_id=org_id,
            org_role=OrgRole.org_member,
        )
        mock_user = create_mock_user(org_id, db_user.id)
        service = TeamService(integration_db_session)

        # Create 10 teams
        teams = []
        for i in range(10):
            team = TeamFactory.create(
                integration_db_session,
                name=f"Team {i:02d}",
                organization_id=org_id,
            )
            teams.append(team)

        # Add user as member to only 3 teams
        for i in [0, 2, 5]:
            TeamMembershipFactory.create(
                session=integration_db_session,
                team_id=teams[i].id,
                user_id=db_user.id,
                role=TeamRole.team_member,
            )

        # Test: Regular user should only see 3 teams they're a member of
        user_teams = service.get_teams(user=mock_user, limit=30, offset=0)
        assert len(user_teams.teams) == 3
        assert user_teams.total == 3

        # Verify it's the correct teams
        team_names = {team.name for team in user_teams.teams}
        assert team_names == {"Team 00", "Team 02", "Team 05"}

    def test_get_teams_search_as_regular_user_only_shows_member_teams(
        self, integration_db_session: Session
    ) -> None:
        """Test that regular users can search but only see teams they are members of."""
        org_id = "test-org-id"

        # Create regular user (not super admin)
        db_user = Auth0UserFactory.create(
            session=integration_db_session,
            user_id="test-regular-user-2",
            email="user2@example.com",
            name="Regular User 2",
            organization_id=org_id,
            org_role=OrgRole.org_member,
        )
        mock_user = create_mock_user(org_id, db_user.id)
        service = TeamService(integration_db_session)

        # Create teams
        eng_team_1 = TeamFactory.create(
            integration_db_session,
            name="Engineering Alpha",
            organization_id=org_id,
        )

        design_team = TeamFactory.create(
            integration_db_session,
            name="Design Team",
            organization_id=org_id,
        )

        # Add user as member to only Engineering Alpha and Design Team
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=eng_team_1.id,
            user_id=db_user.id,
            role=TeamRole.team_member,
        )
        TeamMembershipFactory.create(
            session=integration_db_session,
            team_id=design_team.id,
            user_id=db_user.id,
            role=TeamRole.team_admin,
        )

        # Test: Search for "Engineering" should only return Engineering Alpha (not Beta)
        eng_teams = service.get_teams(
            user=mock_user, search="Engineering", limit=30, offset=0
        )
        assert len(eng_teams.teams) == 1
        assert eng_teams.total == 1
        assert eng_teams.teams[0].name == "Engineering Alpha"

        # Test: List all teams should return 2 teams
        all_teams = service.get_teams(user=mock_user, limit=30, offset=0)
        assert len(all_teams.teams) == 2
        assert all_teams.total == 2
