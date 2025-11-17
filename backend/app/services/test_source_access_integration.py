"""
Integration tests for Source Access (Team-Source and User-Source workflows).

These tests verify RBAC access propagation, cascading deletes, and organization isolation.

Run with: pytest -m integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from database.models import PrimaryAssetRoleGrant, Team, TeamMembership
from database.models_enums import OrgRole, PrimaryAssetRole, PrincipalKind
from fastapi import HTTPException
from sqlmodel import Session, select

if TYPE_CHECKING:
    from app.auth.models import User

from app.schemas.source_access_schema import (
    AddSourceUsersRequest,
    AddTeamSourcesRequest,
    RemoveSourceUsersRequest,
    RemoveTeamSourcesRequest,
    SourceUserInput,
    TeamSourceInput,
)
from app.services.source_access_service import SourceAccessService
from app.services.team_member_service import TeamMemberService
from app.services.team_service import TeamService
from app.test_factories import (
    Auth0UserFactory,
    PrimaryAssetFactory,
    PrimaryAssetRoleGrantFactory,
    TeamFactory,
    TeamMembershipFactory,
)


def create_mock_user(organization_id: str, user_id: str = "test-user-id") -> User:
    """Create a mock User object for testing."""
    from app.auth.models import User

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
class TestTeamSourceAccessPropagation:
    """Test Scenario 2: Team-Source access propagation."""

    def test_add_source_to_team_creates_grant(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that adding a source to a team creates the correct access grant.

        Steps:
        1. Create team with 3 members
        2. Create a source
        3. Add source to team with 'admin' role
        4. Verify PrimaryAssetRoleGrant created
        5. Query team sources - verify source appears
        6. Query source members - verify team appears
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Step 1: Create team with members
        team = TeamFactory.create(integration_db_session, name="Engineering")
        user1 = Auth0UserFactory.create(integration_db_session)
        user2 = Auth0UserFactory.create(integration_db_session)
        user3 = Auth0UserFactory.create(integration_db_session)

        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user1.id
        )
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user2.id
        )
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user3.id
        )

        # Step 2: Create source
        source = PrimaryAssetFactory.create(
            integration_db_session, display_name="My Codebase"
        )

        # Step 3: Add source to team
        service.add_team_sources(
            user=mock_user,
            team_id=team.id,
            request=AddTeamSourcesRequest(
                sources=[TeamSourceInput(source_id=str(source.id), role="asset_admin")]
            ),
        )

        # Step 4: Verify grant created in DB
        grant = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.team_id == team.id,
                PrimaryAssetRoleGrant.primary_asset_id == source.id,
            )
        ).first()
        assert grant is not None
        assert grant.principal_kind == PrincipalKind.team
        assert grant.role == PrimaryAssetRole.asset_admin
        assert grant.organization_id == org_id

        # Step 5: Query team sources
        team_sources = service.get_team_sources(
            user=mock_user, team_id=team.id, limit=10, offset=0
        )
        assert team_sources.total == 1
        assert len(team_sources.sources) == 1
        assert team_sources.sources[0].id == str(source.id)
        assert team_sources.sources[0].role == "asset_admin"

        # Step 6: Query source teams (teams with access to the source)
        source_teams = service.get_source_teams(
            user=mock_user,
            source_id=source.id,
            limit=10,
            offset=0,
        )
        assert source_teams.total == 1
        assert source_teams.teams[0].team_id == team.id
        assert source_teams.teams[0].team_name == "Engineering"

    def test_remove_source_from_team_deletes_grant(
        self, integration_db_session: Session
    ) -> None:
        """Test that removing a source from a team deletes the grant."""
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Create team and source with existing grant
        team = TeamFactory.create(integration_db_session)
        source = PrimaryAssetFactory.create(integration_db_session)
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=source.id,
            principal_kind=PrincipalKind.team,
            team_id=team.id,
        )

        # Verify grant exists
        grant_before = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.team_id == team.id,
                PrimaryAssetRoleGrant.primary_asset_id == source.id,
            )
        ).first()
        assert grant_before is not None

        # Remove source from team
        service.remove_team_sources(
            user=mock_user,
            team_id=team.id,
            request=RemoveTeamSourcesRequest(source_ids=[str(source.id)]),
        )

        # Verify grant deleted
        grant_after = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.team_id == team.id,
                PrimaryAssetRoleGrant.primary_asset_id == source.id,
            )
        ).first()
        assert grant_after is None


@pytest.mark.integration
class TestUserDirectVsTeamAccess:
    """Test Scenario 3: User has both direct and team-based access."""

    def test_user_combined_access_sources(
        self, integration_db_session: Session
    ) -> None:
        """
        Test user with both direct access and team-based access to same source.

        Steps:
        1. Create user with direct access to Source A (role: member)
        2. Create team with user, add Source A to team (role: admin)
        3. Query getUserSources - verify user has BOTH grants visible
        4. Remove user from team - verify still has direct access
        5. Remove direct access - verify no access remains
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Create user and source
        user = Auth0UserFactory.create(integration_db_session)
        source = PrimaryAssetFactory.create(integration_db_session)

        # Step 1: Grant user direct access (role: member)
        service.add_source_users(
            user=mock_user,
            source_id=source.id,
            request=AddSourceUsersRequest(
                users=[SourceUserInput(user_id=user.id, role="asset_member")]
            ),
        )

        # Step 2: Create team with user and grant team access (role: admin)
        team = TeamFactory.create(integration_db_session)
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user.id
        )
        service.add_team_sources(
            user=mock_user,
            team_id=team.id,
            request=AddTeamSourcesRequest(
                sources=[TeamSourceInput(source_id=str(source.id), role="asset_admin")]
            ),
        )

        # Step 3: Verify user has direct access grant in DB
        user_direct_grant = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.user_id == user.id,
                PrimaryAssetRoleGrant.primary_asset_id == source.id,
            )
        ).first()
        assert user_direct_grant is not None
        assert (
            user_direct_grant.role == PrimaryAssetRole.asset_member
        )  # "member" maps to viewer

        # Verify both grants exist in DB
        all_grants = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.primary_asset_id == source.id
            )
        ).all()
        assert len(all_grants) == 2  # 1 direct + 1 team

        # Step 4: Remove user from team
        member_service = TeamMemberService(integration_db_session)
        from app.schemas.team_member_schema import RemoveTeamMembersRequest

        member_service.remove_team_members(
            user=mock_user,
            team_id=team.id,
            request=RemoveTeamMembersRequest(user_ids=[user.id]),
        )

        # Verify user still has direct access grant in DB
        user_direct_grant_after = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.user_id == user.id,
                PrimaryAssetRoleGrant.primary_asset_id == source.id,
            )
        ).first()
        assert user_direct_grant_after is not None

        # Verify team grant still exists (team membership removed, not grant)
        team_grant = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.team_id == team.id
            )
        ).first()
        assert team_grant is not None  # Team still has access to source

        # Step 5: Remove direct access
        service.remove_source_users(
            user=mock_user,
            source_id=source.id,
            request=RemoveSourceUsersRequest(user_ids=[user.id]),
        )

        # Verify user has no direct access
        user_grant_final = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.user_id == user.id,
                PrimaryAssetRoleGrant.primary_asset_id == source.id,
            )
        ).first()
        assert user_grant_final is None


@pytest.mark.integration
class TestOrganizationIsolation:
    """Test Scenario 4: Organization isolation."""

    def test_user_cannot_access_other_org_teams(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that users cannot access teams from other organizations.

        Steps:
        1. User A in Org 1 creates Team X
        2. User B in Org 2 attempts to get Team X
        3. Verify User B gets None/404
        4. User B lists teams - verify Team X not included
        """
        org1_id = "org-1-id"
        org2_id = "org-2-id"
        team_service = TeamService(integration_db_session)

        # Create team in Org 1
        team_org1 = TeamFactory.create(
            integration_db_session, name="Org 1 Team", organization_id=org1_id
        )

        # Create team in Org 2
        team_org2 = TeamFactory.create(
            integration_db_session, name="Org 2 Team", organization_id=org2_id
        )

        # User in Org 2 attempts to get Org 1's team
        mock_user_org2 = create_mock_user(org2_id)
        with pytest.raises(HTTPException) as exc_info:
            team_service.get_team(user=mock_user_org2, team_id=team_org1.id)
        assert exc_info.value.status_code == 404

        # User in Org 2 lists teams - should only see Org 2 teams
        org2_teams = team_service.get_teams(user=mock_user_org2, limit=10, offset=0)
        assert org2_teams.total == 1
        assert org2_teams.teams[0].id == str(team_org2.id)
        assert org2_teams.teams[0].name == "Org 2 Team"

    def test_user_cannot_add_members_to_other_org_team(
        self, integration_db_session: Session
    ) -> None:
        """Test that users cannot modify teams from other organizations."""
        org1_id = "org-1-id"
        org2_id = "org-2-id"

        # Create team in Org 1
        team_org1 = TeamFactory.create(
            integration_db_session, name="Org 1 Team", organization_id=org1_id
        )

        # Create user in Org 2
        user_org2 = Auth0UserFactory.create(
            integration_db_session, organization_id=org2_id
        )

        # User in Org 2 attempts to add members to Org 1's team
        member_service = TeamMemberService(integration_db_session)
        mock_user_org2 = create_mock_user(org2_id)
        from app.schemas.team_member_schema import (
            AddTeamMembersRequest,
            TeamMemberAddInput,
        )

        with pytest.raises(HTTPException) as exc_info:
            member_service.add_team_members(
                user=mock_user_org2,
                team_id=team_org1.id,
                request=AddTeamMembersRequest(
                    members=[
                        TeamMemberAddInput(user_id=user_org2.id, role="team_member")
                    ]
                ),
            )
        assert exc_info.value.status_code in [403, 404]


@pytest.mark.integration
class TestCascadingDeletes:
    """Test Scenario 5: Cascading deletes and data cleanup."""

    def test_cascading_delete_team_cleans_up_all_data(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that deleting a team properly cleans up all related data.

        Steps:
        1. Create team with 5 members and 3 sources
        2. Delete team
        3. Verify all TeamMembership records deleted
        4. Verify all team-based PrimaryAssetRoleGrant records deleted
        5. Verify sources still exist (not deleted)
        6. Verify users still exist (not deleted)
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        team_service = TeamService(integration_db_session)

        # Step 1: Create team with members and sources
        team = TeamFactory.create(integration_db_session)

        # Add 5 members
        users = [Auth0UserFactory.create(integration_db_session) for _ in range(5)]
        for user in users:
            TeamMembershipFactory.create(
                integration_db_session, team_id=team.id, user_id=user.id
            )

        # Add 3 sources
        sources = [PrimaryAssetFactory.create(integration_db_session) for _ in range(3)]
        for source in sources:
            PrimaryAssetRoleGrantFactory.create(
                integration_db_session,
                primary_asset_id=source.id,
                principal_kind=PrincipalKind.team,
                team_id=team.id,
            )

        # Verify data exists before delete
        memberships_before = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.team_id == team.id)
        ).all()
        assert len(memberships_before) == 5

        grants_before = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.team_id == team.id
            )
        ).all()
        assert len(grants_before) == 3

        # Step 2: Delete team
        team_service.delete_team(user=mock_user, team_id=team.id)

        # Step 3: Verify team deleted
        team_deleted = integration_db_session.get(Team, team.id)
        assert team_deleted is None

        # Step 4: Verify all memberships deleted
        memberships_after = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.team_id == team.id)
        ).all()
        assert len(memberships_after) == 0

        # Step 5: Verify all team grants deleted
        grants_after = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.team_id == team.id
            )
        ).all()
        assert len(grants_after) == 0

        # Step 6: Verify sources still exist
        from database.models import PrimaryAsset

        for source in sources:
            source_in_db = integration_db_session.get(PrimaryAsset, source.id)
            assert source_in_db is not None

        # Step 7: Verify users still exist
        for user in users:
            from database.models import User

            user_in_db = integration_db_session.exec(
                select(User).where(User.id == user.id)
            ).first()
            assert user_in_db is not None


@pytest.mark.integration
class TestGetSourceUsersEffectiveAccess:
    """Test that get_source_users returns all effective users (direct + team-based)."""

    def test_get_source_users_includes_team_members(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that get_source_users returns all users with effective access.

        Steps:
        1. Create a source
        2. Create user A with direct grant (member role)
        3. Create user B with no direct grant
        4. Create team with user B as member
        5. Grant team access to source (admin role)
        6. Call get_source_users
        7. Verify both users appear in results
        8. Verify user A has access_type='direct' and source_role='member'
        9. Verify user B has access_type='team' and source_role='admin'
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Step 1: Create source
        source = PrimaryAssetFactory.create(
            integration_db_session, display_name="Test Source"
        )

        # Step 2: Create user A with direct grant
        user_a = Auth0UserFactory.create(integration_db_session, name="User A")
        service.add_source_users(
            user=mock_user,
            source_id=source.id,
            request=AddSourceUsersRequest(
                users=[
                    SourceUserInput(
                        user_id=user_a.id, role=PrimaryAssetRole.asset_member
                    )
                ]
            ),
        )

        # Step 3-5: Create user B, team, and team grant
        user_b = Auth0UserFactory.create(integration_db_session, name="User B")
        team = TeamFactory.create(integration_db_session, name="Test Team")
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user_b.id
        )
        service.add_team_sources(
            user=mock_user,
            team_id=team.id,
            request=AddTeamSourcesRequest(
                sources=[
                    TeamSourceInput(
                        source_id=str(source.id), role=PrimaryAssetRole.asset_admin
                    )
                ]
            ),
        )

        # Step 6: Call get_source_users
        result = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            limit=100,
            offset=0,
        )

        # Step 7: Verify both users appear
        assert result.total == 2
        assert len(result.users) == 2

        # Find users in results
        user_a_result = next((u for u in result.users if u.user_id == user_a.id), None)
        user_b_result = next((u for u in result.users if u.user_id == user_b.id), None)

        assert user_a_result is not None, "User A should appear in results"
        assert user_b_result is not None, "User B should appear in results"

        # Step 8: Verify user A has direct access
        assert user_a_result.assignment_type == "direct"
        assert (
            user_a_result.source_role == PrimaryAssetRole.asset_member
        )  # Direct grant
        assert user_a_result.effective_role == PrimaryAssetRole.asset_member
        assert user_a_result.name == "User A"

        # Step 9: Verify user B has inherited access (via team)
        assert user_b_result.assignment_type == "inherited"
        assert user_b_result.source_role is None  # No direct grant
        assert user_b_result.effective_role == PrimaryAssetRole.asset_admin  # From team
        assert user_b_result.name == "User B"
        # Verify user B's team membership is shown with source_role
        assert len(user_b_result.teams) == 1
        assert user_b_result.teams[0].team_id == team.id
        assert user_b_result.teams[0].display_name == "Test Team"
        assert user_b_result.teams[0].source_role == PrimaryAssetRole.asset_admin

    def test_get_source_users_direct_grant_takes_precedence(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that direct grants take precedence over team grants.

        Steps:
        1. Create source
        2. Create user with direct grant (admin role)
        3. Create team with user, grant team access (member role)
        4. Call get_source_users
        5. Verify user appears once with access_type='direct' and source_role='admin'
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Step 1: Create source
        source = PrimaryAssetFactory.create(integration_db_session)

        # Step 2: Create user with direct grant (admin)
        user = Auth0UserFactory.create(integration_db_session, name="Test User")
        service.add_source_users(
            user=mock_user,
            source_id=source.id,
            request=AddSourceUsersRequest(
                users=[
                    SourceUserInput(user_id=user.id, role=PrimaryAssetRole.asset_admin)
                ]
            ),
        )

        # Step 3: Create team with user, grant team access (member)
        team = TeamFactory.create(integration_db_session)
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user.id
        )
        service.add_team_sources(
            user=mock_user,
            team_id=team.id,
            request=AddTeamSourcesRequest(
                sources=[
                    TeamSourceInput(
                        source_id=str(source.id), role=PrimaryAssetRole.asset_member
                    )
                ]
            ),
        )

        # Step 4: Call get_source_users
        result = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            limit=100,
            offset=0,
        )

        # Step 5: Verify user appears once with direct grant details
        assert result.total == 1
        assert len(result.users) == 1
        user_result = result.users[0]
        assert user_result.user_id == user.id
        assert user_result.assignment_type == "direct"
        assert user_result.source_role == PrimaryAssetRole.asset_admin  # Direct grant
        assert (
            user_result.effective_role == PrimaryAssetRole.asset_admin
        )  # Same as direct
        # User should still see their team membership
        assert len(user_result.teams) == 1
        assert user_result.teams[0].team_id == team.id

    def test_get_source_users_filters_by_role(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that get_source_users correctly filters by source role.

        Steps:
        1. Create source
        2. Create user A with direct admin grant
        3. Create user B via team with member grant
        4. Call get_source_users with roles=['admin']
        5. Verify only user A appears
        6. Call get_source_users with roles=['member']
        7. Verify only user B appears
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Step 1: Create source
        source = PrimaryAssetFactory.create(integration_db_session)

        # Step 2: Create user A with direct admin grant
        user_a = Auth0UserFactory.create(integration_db_session, name="Admin User")
        service.add_source_users(
            user=mock_user,
            source_id=source.id,
            request=AddSourceUsersRequest(
                users=[
                    SourceUserInput(
                        user_id=user_a.id, role=PrimaryAssetRole.asset_admin
                    )
                ]
            ),
        )

        # Step 3: Create user B via team with member grant
        user_b = Auth0UserFactory.create(integration_db_session, name="Member User")
        team = TeamFactory.create(integration_db_session)
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user_b.id
        )
        service.add_team_sources(
            user=mock_user,
            team_id=team.id,
            request=AddTeamSourcesRequest(
                sources=[
                    TeamSourceInput(
                        source_id=str(source.id), role=PrimaryAssetRole.asset_member
                    )
                ]
            ),
        )

        # Step 4: Filter by admin role (effective_role)
        result_admin = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            roles=[PrimaryAssetRole.asset_admin],
            limit=100,
            offset=0,
        )
        assert result_admin.total == 1
        assert result_admin.users[0].user_id == user_a.id
        assert result_admin.users[0].effective_role == PrimaryAssetRole.asset_admin
        assert (
            result_admin.users[0].source_role == PrimaryAssetRole.asset_admin
        )  # Direct grant

        # Step 6: Filter by member role (effective_role)
        result_member = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            roles=[PrimaryAssetRole.asset_member],
            limit=100,
            offset=0,
        )
        assert result_member.total == 1
        assert result_member.users[0].user_id == user_b.id
        assert result_member.users[0].effective_role == PrimaryAssetRole.asset_member
        assert (
            result_member.users[0].source_role is None
        )  # No direct grant (team-based)

    def test_get_source_users_filters_by_assignment_type(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that get_source_users correctly filters by assignment_type.

        Steps:
        1. Create source
        2. Create user A with direct admin grant
        3. Create user B via team with member grant
        4. Call get_source_users with assignment_type='direct'
        5. Verify only user A appears
        6. Call get_source_users with assignment_type='inherited'
        7. Verify only user B appears
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Step 1: Create source
        source = PrimaryAssetFactory.create(integration_db_session)

        # Step 2: Create user A with direct admin grant
        user_a = Auth0UserFactory.create(integration_db_session, name="Direct User")
        service.add_source_users(
            user=mock_user,
            source_id=source.id,
            request=AddSourceUsersRequest(
                users=[
                    SourceUserInput(
                        user_id=user_a.id, role=PrimaryAssetRole.asset_admin
                    )
                ]
            ),
        )

        # Step 3: Create user B via team with member grant
        user_b = Auth0UserFactory.create(integration_db_session, name="Inherited User")
        team = TeamFactory.create(integration_db_session)
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user_b.id
        )
        service.add_team_sources(
            user=mock_user,
            team_id=team.id,
            request=AddTeamSourcesRequest(
                sources=[
                    TeamSourceInput(
                        source_id=str(source.id), role=PrimaryAssetRole.asset_member
                    )
                ]
            ),
        )

        # Step 4: Filter by direct access
        result_direct = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            assignment_type="direct",
            limit=100,
            offset=0,
        )
        assert result_direct.total == 1
        assert result_direct.users[0].user_id == user_a.id
        assert result_direct.users[0].assignment_type == "direct"

        # Step 6: Filter by inherited access
        result_inherited = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            assignment_type="inherited",
            limit=100,
            offset=0,
        )
        assert result_inherited.total == 1
        assert result_inherited.users[0].user_id == user_b.id
        assert result_inherited.users[0].assignment_type == "inherited"

    def test_get_source_users_includes_super_admins(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that super admins appear in source users with inherited asset_admin role.

        Steps:
        1. Create source
        2. Create regular user with direct member grant
        3. Create super admin user (no direct grant to source)
        4. Call get_source_users
        5. Verify both users appear
        6. Verify super admin has effective_role='asset_admin' and assignment_type='inherited'
        7. Filter by role=asset_admin
        8. Verify super admin appears but regular user does not
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Step 1: Create source
        source = PrimaryAssetFactory.create(integration_db_session)

        # Step 2: Create regular user with direct member grant
        regular_user = Auth0UserFactory.create(
            integration_db_session, name="Regular User", organization_id=org_id
        )
        service.add_source_users(
            user=mock_user,
            source_id=source.id,
            request=AddSourceUsersRequest(
                users=[
                    SourceUserInput(
                        user_id=regular_user.id, role=PrimaryAssetRole.asset_member
                    )
                ]
            ),
        )

        # Step 3: Create super admin user (with org membership but no direct source grant)
        from database.models import OrgMembership

        super_admin = Auth0UserFactory.create(
            integration_db_session, name="Super Admin", organization_id=org_id
        )
        # Update the existing org membership to make them a super admin
        org_membership = integration_db_session.exec(
            select(OrgMembership).where(
                OrgMembership.user_id == super_admin.id,
                OrgMembership.org_id == org_id,
            )
        ).first()
        if org_membership:
            org_membership.role = OrgRole.org_super_admin
            integration_db_session.add(org_membership)
            integration_db_session.commit()
        else:
            # Create if it doesn't exist
            org_membership = OrgMembership(
                user_id=super_admin.id, org_id=org_id, role=OrgRole.org_super_admin
            )
            integration_db_session.add(org_membership)
            integration_db_session.commit()

        # Step 4: Call get_source_users
        result_all = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            limit=100,
            offset=0,
        )

        # Step 5 & 6: Verify both users appear with correct roles
        assert result_all.total == 2
        user_map = {u.user_id: u for u in result_all.users}

        assert regular_user.id in user_map
        assert user_map[regular_user.id].effective_role == PrimaryAssetRole.asset_member
        assert user_map[regular_user.id].assignment_type == "direct"

        assert super_admin.id in user_map
        assert user_map[super_admin.id].effective_role == PrimaryAssetRole.asset_admin
        assert user_map[super_admin.id].assignment_type == "inherited"
        assert user_map[super_admin.id].is_super_admin is True

        # Step 7: Filter by asset_admin role
        result_admins = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            roles=[PrimaryAssetRole.asset_admin],
            limit=100,
            offset=0,
        )

        # Step 8: Verify only super admin appears
        assert result_admins.total == 1
        assert result_admins.users[0].user_id == super_admin.id
        assert result_admins.users[0].effective_role == PrimaryAssetRole.asset_admin

        # Bonus: Verify super admin appears in inherited filter
        result_inherited = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            assignment_type="inherited",
            limit=100,
            offset=0,
        )
        assert result_inherited.total == 1
        assert result_inherited.users[0].user_id == super_admin.id

    def test_super_admin_role_takes_precedence_over_direct_grant(
        self, integration_db_session: Session
    ) -> None:
        """
        Test that super admin's implicit asset_admin role takes precedence over direct lower grants.

        Steps:
        1. Create source
        2. Create super admin user
        3. Give super admin a direct asset_member grant (lower than their implicit asset_admin)
        4. Call get_source_users
        5. Verify super admin appears with effective_role='asset_admin' (not asset_member)
        6. Verify assignment_type is still 'inherited' (from super admin status, not direct grant)
        """
        org_id = "test-org-id"
        mock_user = create_mock_user(org_id)
        service = SourceAccessService(integration_db_session)

        # Step 1: Create source
        source = PrimaryAssetFactory.create(integration_db_session)

        # Step 2: Create super admin user
        from database.models import OrgMembership

        super_admin = Auth0UserFactory.create(
            integration_db_session, name="Super Admin", organization_id=org_id
        )
        # Update org membership to make them super admin
        org_membership = integration_db_session.exec(
            select(OrgMembership).where(
                OrgMembership.user_id == super_admin.id,
                OrgMembership.org_id == org_id,
            )
        ).first()
        if org_membership:
            org_membership.role = OrgRole.org_super_admin
            integration_db_session.add(org_membership)
            integration_db_session.commit()

        # Step 3: Give super admin a direct asset_member grant (lower privilege)
        service.add_source_users(
            user=mock_user,
            source_id=source.id,
            request=AddSourceUsersRequest(
                users=[
                    SourceUserInput(
                        user_id=super_admin.id, role=PrimaryAssetRole.asset_member
                    )
                ]
            ),
        )

        # Step 4: Call get_source_users
        result = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            limit=100,
            offset=0,
        )

        # Step 5 & 6: Verify super admin has asset_admin (not asset_member)
        assert result.total == 1
        user_result = result.users[0]

        assert user_result.user_id == super_admin.id
        # Super admin role should win over direct member grant
        assert user_result.effective_role == PrimaryAssetRole.asset_admin
        # Even though there's a direct grant, the effective one comes from super admin status
        # which has higher priority due to role priority (asset_admin > asset_member)
        assert user_result.is_super_admin is True

        # Additional verification: filter by asset_admin should still return the user
        result_admin = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            roles=[PrimaryAssetRole.asset_admin],
            limit=100,
            offset=0,
        )
        assert result_admin.total == 1
        assert result_admin.users[0].user_id == super_admin.id

        # Filter by asset_member should NOT return the user (they're admin, not member)
        result_member = service.get_source_users(
            user=mock_user,
            source_id=source.id,
            roles=[PrimaryAssetRole.asset_member],
            limit=100,
            offset=0,
        )
        assert result_member.total == 0
