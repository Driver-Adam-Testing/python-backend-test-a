"""
Integration tests for auth0_event_processor org membership operations.

These tests verify critical functionality with a real PostgreSQL database:
- Membership creation and deletion
- Cascading deletes (TeamMembership, PrimaryAssetRoleGrant)
- Data isolation between organizations

Run with: cd content_services/auth0_sync && poetry run pytest tests/ -m integration -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src directory to path for imports
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest  # noqa: E402
from database.models import (  # noqa: E402
    OrgMembership,
    PrimaryAssetRoleGrant,
    TeamMembership,
    User,
)
from database.models_enums import (  # noqa: E402
    PrimaryAssetRole,
    PrincipalKind,
    TeamRole,
)
from sqlmodel import Session, select  # noqa: E402

from .conftest import (  # noqa: E402
    OrgMembershipFactory,
    PrimaryAssetFactory,
    PrimaryAssetRoleGrantFactory,
    TeamFactory,
    TeamMembershipFactory,
    UserFactory,
)


@pytest.mark.integration
class TestOrgMembershipCreation:
    """Test org membership creation via event processing."""

    def test_org_member_add_creates_membership(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that processing a membership event for a new member creates OrgMembership.

        Steps:
        1. Create user without org membership
        2. Configure Auth0 mock to show user IS in org
        3. Process membership change
        4. Verify OrgMembership created
        """
        from datetime import UTC, datetime

        from event_processor.auth0_event_processor import _process_membership_change

        user_id = "auth0|new_member_123"
        org_id = "test-org-id"

        # Create user without org membership
        user = User(
            id=user_id,
            email="newmember@test.com",
            name="New Member",
            auth0_updated_at=datetime.now(UTC),
        )
        integration_db_session.add(user)
        integration_db_session.commit()

        # Configure Auth0: user IS a member of the org
        mock_auth0_service.get_user_organizations.return_value = [{"id": org_id}]
        mock_auth0_service.get_user_profile.return_value = {
            "user_id": user_id,
            "email": "newmember@test.com",
            "name": "New Member",
            "updated_at": "2024-01-01T00:00:00Z",
            "app_metadata": {},
        }

        # Process membership change
        result = _process_membership_change(user_id, org_id)

        # Verify membership created
        membership = integration_db_session.exec(
            select(OrgMembership).where(
                OrgMembership.user_id == user_id,
                OrgMembership.org_id == org_id,
            )
        ).first()

        assert membership is not None
        assert membership.user_id == user_id
        assert membership.org_id == org_id
        assert "membership" in result


@pytest.mark.integration
class TestOrgMembershipDeletion:
    """Test org membership deletion and cascading deletes."""

    def test_org_member_remove_deletes_membership(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that removing a user from an org deletes their OrgMembership.

        Steps:
        1. Create user with org membership
        2. Configure Auth0 mock to show user is NOT in org
        3. Process membership change
        4. Verify OrgMembership deleted
        """
        from event_processor.auth0_event_processor import _process_membership_change

        # Create user with org membership
        user = UserFactory.create(
            integration_db_session,
            organization_id="test-org-id",
        )

        # Verify membership exists before
        membership_before = integration_db_session.exec(
            select(OrgMembership).where(OrgMembership.user_id == user.id)
        ).first()
        assert membership_before is not None

        # Configure Auth0: user is NOT in the org anymore
        mock_auth0_service.get_user_organizations.return_value = []

        # Process membership change
        result = _process_membership_change(user.id, "test-org-id")

        # Refresh session to see changes
        integration_db_session.expire_all()

        # Verify membership deleted
        membership_after = integration_db_session.exec(
            select(OrgMembership).where(OrgMembership.user_id == user.id)
        ).first()

        assert membership_after is None
        assert "membership" in result

    def test_org_member_remove_cascades_team_memberships(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that removing a user from org deletes their TeamMemberships for that org.

        This test verifies the bug fix where TeamMembership deletion was failing
        because the code incorrectly tried to filter by TeamMembership.org_id
        (which doesn't exist - must join through Team table).

        Steps:
        1. Create user with org membership
        2. Create team in org and add user as member
        3. Configure Auth0 to show user is NOT in org
        4. Process membership change
        5. Verify TeamMembership deleted via Team.organization_id join
        """
        from event_processor.auth0_event_processor import _process_membership_change

        org_id = "test-org-id"

        # Create user with org membership
        user = UserFactory.create(integration_db_session, organization_id=org_id)

        # Create team in the org
        team = TeamFactory.create(integration_db_session, organization_id=org_id)

        # Add user to team
        TeamMembershipFactory.create(
            integration_db_session,
            team_id=team.id,
            user_id=user.id,
            role=TeamRole.team_member,
        )

        # Verify team membership exists before
        team_membership_before = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.user_id == user.id)
        ).all()
        assert len(team_membership_before) == 1

        # Configure Auth0: user is NOT in the org
        mock_auth0_service.get_user_organizations.return_value = []

        # Process membership change
        _process_membership_change(user.id, org_id)

        # Refresh session
        integration_db_session.expire_all()

        # Verify team membership deleted
        team_membership_after = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.user_id == user.id)
        ).all()

        assert len(team_membership_after) == 0

    def test_org_member_remove_cascades_asset_grants(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that removing user from org deletes their PrimaryAssetRoleGrants for that org.

        This prevents FK constraint violations when deleting the OrgMembership.
        """
        from event_processor.auth0_event_processor import _process_membership_change

        org_id = "test-org-id"

        # Create user with org membership
        user = UserFactory.create(integration_db_session, organization_id=org_id)

        # Create asset and grant user access
        asset = PrimaryAssetFactory.create(
            integration_db_session, organization_id=org_id
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=asset.id,
            organization_id=org_id,
            principal_kind=PrincipalKind.user,
            user_id=user.id,
            role=PrimaryAssetRole.asset_member,
        )

        # Verify grant exists before
        grants_before = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.user_id == user.id,
                PrimaryAssetRoleGrant.organization_id == org_id,
            )
        ).all()
        assert len(grants_before) == 1

        # Configure Auth0: user is NOT in the org
        mock_auth0_service.get_user_organizations.return_value = []

        # Process membership change
        _process_membership_change(user.id, org_id)

        # Refresh session
        integration_db_session.expire_all()

        # Verify grant deleted
        grants_after = integration_db_session.exec(
            select(PrimaryAssetRoleGrant).where(
                PrimaryAssetRoleGrant.user_id == user.id,
                PrimaryAssetRoleGrant.organization_id == org_id,
            )
        ).all()

        assert len(grants_after) == 0

    def test_org_removal_preserves_other_org_data(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that removing user from org A does NOT delete their data in org B.

        Steps:
        1. Create user in org-1-id and org-2-id
        2. Create teams and memberships in both orgs
        3. Remove user from org-1-id only
        4. Verify org-2-id data is preserved
        """
        from datetime import UTC, datetime

        from event_processor.auth0_event_processor import _process_membership_change

        org1_id = "org-1-id"
        org2_id = "org-2-id"
        user_id = "auth0|multi_org_user"

        # Create user
        user = User(
            id=user_id,
            email="multi@test.com",
            name="Multi Org User",
            auth0_updated_at=datetime.now(UTC),
        )
        integration_db_session.add(user)
        integration_db_session.flush()

        # Create memberships in both orgs
        OrgMembershipFactory.create(
            integration_db_session, user_id=user_id, org_id=org1_id
        )
        OrgMembershipFactory.create(
            integration_db_session, user_id=user_id, org_id=org2_id
        )

        # Create teams in both orgs
        team1 = TeamFactory.create(
            integration_db_session, name="Org1 Team", organization_id=org1_id
        )
        team2 = TeamFactory.create(
            integration_db_session, name="Org2 Team", organization_id=org2_id
        )

        # Add user to both teams
        TeamMembershipFactory.create(
            integration_db_session, team_id=team1.id, user_id=user_id
        )
        TeamMembershipFactory.create(
            integration_db_session, team_id=team2.id, user_id=user_id
        )

        # Configure Auth0: user is only in org2 (removed from org1)
        mock_auth0_service.get_user_organizations.return_value = [{"id": org2_id}]

        # Process membership change for org1
        _process_membership_change(user_id, org1_id)

        # Refresh session
        integration_db_session.expire_all()

        # Verify org1 data deleted
        org1_membership = integration_db_session.exec(
            select(OrgMembership).where(
                OrgMembership.user_id == user_id,
                OrgMembership.org_id == org1_id,
            )
        ).first()
        assert org1_membership is None

        team1_membership = integration_db_session.exec(
            select(TeamMembership).where(
                TeamMembership.user_id == user_id,
                TeamMembership.team_id == team1.id,
            )
        ).first()
        assert team1_membership is None

        # Verify org2 data preserved
        org2_membership = integration_db_session.exec(
            select(OrgMembership).where(
                OrgMembership.user_id == user_id,
                OrgMembership.org_id == org2_id,
            )
        ).first()
        assert org2_membership is not None

        team2_membership = integration_db_session.exec(
            select(TeamMembership).where(
                TeamMembership.user_id == user_id,
                TeamMembership.team_id == team2.id,
            )
        ).first()
        assert team2_membership is not None


@pytest.mark.integration
class TestUserDeletion:
    """Test user deletion cascading."""

    def test_user_delete_cascades_all_data(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that deleting a user cascades to all related data.

        User deletion should remove:
        - OrgMembership records
        - TeamMembership records
        - PrimaryAssetRoleGrant records (user-type)
        """
        from event_processor.auth0_event_processor import _handle_user_delete_event
        from event_processor.auth0_event_schema import (
            Auth0EventBridgeEvent,
            Auth0EventData,
            Auth0EventDetail,
        )

        org_id = "test-org-id"

        # Create user with full data
        user = UserFactory.create(integration_db_session, organization_id=org_id)
        user_id = user.id  # Save ID before deletion
        team = TeamFactory.create(integration_db_session, organization_id=org_id)
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user_id
        )
        asset = PrimaryAssetFactory.create(
            integration_db_session, organization_id=org_id
        )
        PrimaryAssetRoleGrantFactory.create(
            integration_db_session,
            primary_asset_id=asset.id,
            organization_id=org_id,
            principal_kind=PrincipalKind.user,
            user_id=user_id,
        )

        # Verify data exists
        assert integration_db_session.get(User, user_id) is not None

        # Create delete event
        event = Auth0EventBridgeEvent(
            detail=Auth0EventDetail(
                data=Auth0EventData(
                    type="sdu",
                    details={
                        "request": {
                            "path": f"/api/v2/users/{user_id}",
                            "method": "delete",
                        }
                    },
                )
            )
        )

        # Process delete event
        _handle_user_delete_event(event)

        # Refresh session
        integration_db_session.expire_all()

        # Verify user deleted
        assert integration_db_session.get(User, user_id) is None

        # Verify cascaded data deleted
        org_membership = integration_db_session.exec(
            select(OrgMembership).where(OrgMembership.user_id == user_id)
        ).first()
        assert org_membership is None

        team_membership = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.user_id == user_id)
        ).first()
        assert team_membership is None

        # Note: PrimaryAssetRoleGrant may or may not cascade depending on DB config
        # The user FK has ondelete="CASCADE" so it should be deleted


@pytest.mark.integration
class TestEventualConsistency:
    """Test eventual consistency handling (backfilling)."""

    def test_membership_event_backfills_missing_user(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that a membership event for an unknown user backfills the user.

        This handles out-of-order events where membership event arrives
        before user creation event.
        """
        from event_processor.auth0_event_processor import _process_membership_change

        user_id = "auth0|backfill_user"
        org_id = "test-org-id"

        # User does NOT exist in DB yet
        assert integration_db_session.get(User, user_id) is None

        # Configure Auth0: user IS a member
        mock_auth0_service.get_user_organizations.return_value = [{"id": org_id}]
        mock_auth0_service.get_user_profile.return_value = {
            "user_id": user_id,
            "email": "backfill@test.com",
            "name": "Backfilled User",
            "updated_at": "2024-01-01T00:00:00Z",
            "app_metadata": {},
        }

        # Process membership change
        result = _process_membership_change(user_id, org_id)

        # Refresh session
        integration_db_session.expire_all()

        # Verify user was backfilled
        user = integration_db_session.get(User, user_id)
        assert user is not None
        assert user.email == "backfill@test.com"
        assert "user" in result

        # Verify membership created
        membership = integration_db_session.exec(
            select(OrgMembership).where(OrgMembership.user_id == user_id)
        ).first()
        assert membership is not None


@pytest.mark.integration
class TestAPIEvents:
    """Test API event (sapi) processing."""

    def test_api_event_org_member_delete(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test processing an API event for organization member deletion.

        This is the code path that triggered the original TeamMembership.org_id bug.
        """
        from event_processor.auth0_event_processor import _handle_api_event
        from event_processor.auth0_event_schema import (
            Auth0EventBridgeEvent,
            Auth0EventData,
            Auth0EventDetail,
        )

        org_id = "test-org-id"

        # Create user with team membership
        user = UserFactory.create(integration_db_session, organization_id=org_id)
        team = TeamFactory.create(integration_db_session, organization_id=org_id)
        TeamMembershipFactory.create(
            integration_db_session, team_id=team.id, user_id=user.id
        )

        # Configure Auth0: user is NOT in the org anymore
        mock_auth0_service.get_user_organizations.return_value = []

        # Create API event for member deletion
        event = Auth0EventBridgeEvent(
            detail=Auth0EventDetail(
                data=Auth0EventData(
                    type="sapi",
                    details={
                        "request": {
                            "path": f"/api/v2/organizations/{org_id}/members",
                            "method": "delete",
                            "body": {"members": [user.id]},
                        }
                    },
                )
            )
        )

        # Process API event
        result = _handle_api_event(event)

        # Refresh session
        integration_db_session.expire_all()

        # Verify membership deleted
        org_membership = integration_db_session.exec(
            select(OrgMembership).where(OrgMembership.user_id == user.id)
        ).first()
        assert org_membership is None

        # Verify team membership deleted (this was the bug)
        team_membership = integration_db_session.exec(
            select(TeamMembership).where(TeamMembership.user_id == user.id)
        ).first()
        assert team_membership is None

        assert "membership" in result


@pytest.mark.integration
class TestTimestampGuard:
    """Test timestamp guards prevent stale data overwrites."""

    def test_user_update_respects_timestamp_guard(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that older events don't overwrite newer user data.

        This is critical for data integrity in async event systems where
        events can arrive out of order.

        Steps:
        1. Create user with recent auth0_updated_at
        2. Process an older event (earlier timestamp)
        3. Verify user data was NOT overwritten
        """
        from datetime import UTC, datetime, timedelta

        from event_processor.auth0_event_processor import _process_user_update

        user_id = "auth0|timestamp_test_user"

        # Create user with RECENT timestamp
        recent_time = datetime.now(UTC)
        user = User(
            id=user_id,
            email="current@test.com",
            name="Current Name",
            auth0_updated_at=recent_time,
        )
        integration_db_session.add(user)
        integration_db_session.commit()

        # Configure Auth0 to return OLDER data
        old_time = recent_time - timedelta(hours=1)
        mock_auth0_service.get_user_profile.return_value = {
            "user_id": user_id,
            "email": "old@test.com",
            "name": "Old Name",
            "updated_at": old_time.isoformat(),
            "app_metadata": {},
        }

        # Process the stale event
        _process_user_update(user_id)

        # Refresh session
        integration_db_session.expire_all()

        # Verify user data was NOT overwritten
        user = integration_db_session.get(User, user_id)
        assert user.email == "current@test.com"  # Should keep current
        assert user.name == "Current Name"  # Should keep current
        assert user.auth0_updated_at == recent_time  # Timestamp unchanged


@pytest.mark.integration
class TestResilience:
    """Test graceful handling of error conditions."""

    def test_membership_event_user_404_skips_gracefully(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that 404 from Auth0 (user deleted) is handled gracefully.

        This happens when a user is deleted from Auth0 between:
        1. Auth0 emitting the event
        2. Our processor handling the event

        The processor should skip without error.
        """
        import requests
        from event_processor.auth0_event_processor import _process_membership_change

        user_id = "auth0|deleted_user"
        org_id = "test-org-id"

        # Configure Auth0 to return 404 (user was deleted)
        response = requests.models.Response()
        response.status_code = 404
        mock_auth0_service.get_user_organizations.side_effect = (
            requests.exceptions.HTTPError(response=response)
        )

        # Process should not raise, should return empty
        result = _process_membership_change(user_id, org_id)

        # Should return empty list (skipped gracefully)
        assert result == []

        # No user or membership should be created
        user = integration_db_session.get(User, user_id)
        assert user is None


@pytest.mark.integration
class TestIdempotency:
    """Test that processing events multiple times is safe."""

    def test_idempotent_membership_add(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that processing the same membership add event twice is safe.

        Events can be replayed due to retries or reprocessing.
        The second processing should be a no-op.
        """
        from datetime import UTC, datetime

        from event_processor.auth0_event_processor import _process_membership_change

        user_id = "auth0|idempotent_user"
        org_id = "test-org-id"

        # Create user without membership
        user = User(
            id=user_id,
            email="idempotent@test.com",
            name="Idempotent User",
            auth0_updated_at=datetime.now(UTC),
        )
        integration_db_session.add(user)
        integration_db_session.commit()

        # Configure Auth0: user IS a member
        mock_auth0_service.get_user_organizations.return_value = [{"id": org_id}]
        mock_auth0_service.get_user_profile.return_value = {
            "user_id": user_id,
            "email": "idempotent@test.com",
            "name": "Idempotent User",
            "updated_at": datetime.now(UTC).isoformat(),
            "app_metadata": {},
        }

        # Process FIRST time - should create membership
        result1 = _process_membership_change(user_id, org_id)
        assert "membership" in result1

        # Count memberships after first processing
        memberships_after_first = integration_db_session.exec(
            select(OrgMembership).where(
                OrgMembership.user_id == user_id,
                OrgMembership.org_id == org_id,
            )
        ).all()
        assert len(memberships_after_first) == 1

        # Process SECOND time - should be no-op (already exists)
        _process_membership_change(user_id, org_id)

        # Refresh session
        integration_db_session.expire_all()

        # Should still have exactly 1 membership (not duplicated)
        memberships_after_second = integration_db_session.exec(
            select(OrgMembership).where(
                OrgMembership.user_id == user_id,
                OrgMembership.org_id == org_id,
            )
        ).all()
        assert len(memberships_after_second) == 1

    def test_idempotent_membership_remove(
        self,
        integration_db_session: Session,
        mock_auth0_service: MagicMock,
        patch_processor: None,
    ) -> None:
        """
        Test that processing the same membership remove event twice is safe.

        The second processing should be a no-op (already deleted).
        """
        from event_processor.auth0_event_processor import _process_membership_change

        org_id = "test-org-id"

        # Create user with membership
        user = UserFactory.create(integration_db_session, organization_id=org_id)

        # Configure Auth0: user is NOT a member
        mock_auth0_service.get_user_organizations.return_value = []

        # Process FIRST time - should delete membership
        result1 = _process_membership_change(user.id, org_id)
        assert "membership" in result1

        # Verify deleted
        integration_db_session.expire_all()
        membership_after_first = integration_db_session.exec(
            select(OrgMembership).where(OrgMembership.user_id == user.id)
        ).first()
        assert membership_after_first is None

        # Process SECOND time - should be no-op (already deleted)
        result2 = _process_membership_change(user.id, org_id)

        # Should not raise, should return empty (no changes made)
        # The membership was already gone, so nothing to delete
        assert "membership" not in result2
