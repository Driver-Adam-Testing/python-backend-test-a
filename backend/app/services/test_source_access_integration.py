"""
Integration tests for Source Access (Team-Source and User-Source workflows).

These tests verify RBAC access propagation, cascading deletes, and organization isolation.

Run with: pytest -m integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from database.models import PrimaryAssetRoleGrant, Team, TeamMembership
from database.models_enums import PrimaryAssetRole, PrincipalKind
from fastapi import HTTPException
from sqlmodel import Session, select

if TYPE_CHECKING:
    from app.auth.models import User

from app.schemas.source_access_schema import (
    AddSourceMembersRequest,
    AddTeamSourcesRequest,
    RemoveSourceMemberInput,
    RemoveSourceMembersRequest,
    RemoveTeamSourcesRequest,
    SourceMemberInput,
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
                sources=[TeamSourceInput(source_id=str(source.id), role="admin")]
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
        assert grant.role == PrimaryAssetRole.admin
        assert grant.organization_id == org_id

        # Step 5: Query team sources
        team_sources = service.get_team_sources(
            user=mock_user, team_id=team.id, limit=10, offset=0
        )
        assert team_sources.total == 1
        assert len(team_sources.sources) == 1
        assert team_sources.sources[0].id == str(source.id)
        assert team_sources.sources[0].role == "admin"

        # Step 6: Query source members
        source_members = service.get_source_members(
            user=mock_user, source_id=source.id, limit=10, offset=0
        )
        assert source_members.total == 1
        assert source_members.members[0].member_id == str(team.id)
        assert source_members.members[0].kind == "team"
        assert source_members.members[0].source_role == "admin"

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
        service.add_source_members(
            user=mock_user,
            source_id=source.id,
            request=AddSourceMembersRequest(
                members=[
                    SourceMemberInput(member_id=user.id, kind="user", role="member")
                ]
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
                sources=[TeamSourceInput(source_id=str(source.id), role="admin")]
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
            user_direct_grant.role == PrimaryAssetRole.viewer
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
        service.remove_source_members(
            user=mock_user,
            source_id=source.id,
            request=RemoveSourceMembersRequest(
                members=[RemoveSourceMemberInput(member_id=user.id, kind="user")]
            ),
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
                    members=[TeamMemberAddInput(user_id=user_org2.id, role="member")]
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
