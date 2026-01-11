import pytest
from database.models import OrgMembership, TeamMembership
from sqlmodel import Session, select

from app.repositories.user_repository import delete_organization_membership
from app.test_factories import Auth0UserFactory, TeamFactory, TeamMembershipFactory


@pytest.mark.integration
def test_delete_organization_membership_removes_team_memberships(
    integration_db_session: Session,
) -> None:
    # Setup
    org_id = "test-org-id"
    user = Auth0UserFactory.create(integration_db_session, organization_id=org_id)
    team = TeamFactory.create(integration_db_session, organization_id=org_id)

    # Create team membership
    team_membership = TeamMembershipFactory.create(
        integration_db_session, team_id=team.id, user_id=user.id
    )

    # Get the org membership created by factory
    org_membership = integration_db_session.exec(
        select(OrgMembership).where(
            OrgMembership.user_id == user.id, OrgMembership.org_id == org_id
        )
    ).first()

    assert org_membership is not None
    assert integration_db_session.get(TeamMembership, team_membership.id) is not None

    # Execute
    delete_organization_membership(integration_db_session, org_membership)

    # Verify
    assert integration_db_session.get(OrgMembership, org_membership.id) is None
    assert integration_db_session.get(TeamMembership, team_membership.id) is None
