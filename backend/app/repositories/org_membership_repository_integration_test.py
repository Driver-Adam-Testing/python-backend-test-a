"""
Quick integration test for organization users list endpoint changes.
Run with: cd backend && poetry run pytest -m integration app/test_org_users_integration.py -v
"""

import pytest
from app.repositories.org_membership_repository import list_organization_members
from app.test_factories import Auth0UserFactory
from database.models_enums import OrgRole
from sqlmodel import Session


@pytest.mark.integration
def test_list_organization_members_with_search_and_roles(
    integration_db_session: Session,
) -> None:
    """Test list_organization_members with search and role filtering."""
    org_id = "test-org-id"

    Auth0UserFactory.create(
        integration_db_session,
        name="Alice Admin",
        email="alice@example.com",
        organization_id=org_id,
        org_role=OrgRole.org_super_admin,
    )
    Auth0UserFactory.create(
        integration_db_session,
        name="Bob Member",
        email="bob@example.com",
        organization_id=org_id,
        org_role=OrgRole.org_member,
    )
    Auth0UserFactory.create(
        integration_db_session,
        name="Charlie Member",
        email="charlie@example.com",
        organization_id=org_id,
        org_role=OrgRole.org_member,
    )

    # Test 1: No filters - should return all 3 members
    members, total = list_organization_members(integration_db_session, org_id)
    assert total == 3
    assert len(members) == 3

    # Test 2: Limit and offset
    members, total = list_organization_members(
        integration_db_session, org_id, limit=2, offset=0
    )
    assert total == 3
    assert len(members) == 2

    members, total = list_organization_members(
        integration_db_session, org_id, limit=2, offset=2
    )
    assert total == 3
    assert len(members) == 1

    # Test 3: Search by name
    members, total = list_organization_members(
        integration_db_session, org_id, search="alice"
    )
    assert total == 1
    assert members[0]["name"] == "Alice Admin"

    # Test 4: Search by email
    members, total = list_organization_members(
        integration_db_session, org_id, search="bob@"
    )
    assert total == 1
    assert members[0]["email"] == "bob@example.com"

    # Test 5: Search with no match
    members, total = list_organization_members(
        integration_db_session, org_id, search="nonexistent"
    )
    assert total == 0
    assert len(members) == 0

    # Test 6: Filter by single role
    members, total = list_organization_members(
        integration_db_session, org_id, roles=[OrgRole.org_super_admin]
    )
    assert total == 1
    assert members[0]["name"] == "Alice Admin"
    assert members[0]["role"] == OrgRole.org_super_admin.value

    # Test 7: Filter by member role
    members, total = list_organization_members(
        integration_db_session, org_id, roles=[OrgRole.org_member]
    )
    assert total == 2
    names = [m["name"] for m in members]
    assert "Bob Member" in names
    assert "Charlie Member" in names

    # Test 8: Combine search and role filter
    members, total = list_organization_members(
        integration_db_session, org_id, search="admin", roles=[OrgRole.org_super_admin]
    )
    assert total == 1
    assert members[0]["name"] == "Alice Admin"

    # Test 9: Search + role with match
    members, total = list_organization_members(
        integration_db_session, org_id, search="bob", roles=[OrgRole.org_member]
    )
    assert total == 1
    assert members[0]["name"] == "Bob Member"
