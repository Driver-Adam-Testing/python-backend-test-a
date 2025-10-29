"""Unit tests for OrganizationsService business logic."""

from unittest.mock import MagicMock, patch

import pytest
from database.models_enums import OrgRole

from app.api.auth import UserToken
from app.services.organizations_service import OrganizationsService


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def service(session: MagicMock) -> OrganizationsService:
    """Create an OrganizationsService instance."""
    return OrganizationsService(session)


@pytest.fixture
def org_id() -> str:
    """Return a test organization ID."""
    return "org_123"


@pytest.fixture
def user_token(org_id: str) -> UserToken:
    """Create a mock user token."""
    return UserToken.model_construct(
        organization_id=org_id,
        organization_display_name="Test Org",
        organization_name="test-org",
        user_id="auth0|user123",
        issuer="https://test.auth0.com/",
        subject="auth0|user123",
        audience=["https://api.example.com"],
        issued_at=1234567890,
        expiration=1234571490,
        scope="openid profile email",
        authorized_party="client123",
        permissions=["users.view"],
        email="user@example.com",
        full_name="Test User",
    )


@pytest.mark.unit
class TestListMembers:
    """Tests for list_members method."""

    @patch("app.services.organizations_service.list_organization_members")
    def test_list_members_empty_organization(
        self,
        mock_list_org_members: MagicMock,
        service: OrganizationsService,
        user_token: UserToken,
        session: MagicMock,
    ) -> None:
        """Test listing members when organization has no members."""
        mock_list_org_members.return_value = ([], 0)

        result = service.list_members(user_token, page=0, per_page=100)

        assert result.members == []
        assert result.start == 0
        assert result.limit == 100
        assert result.total == 0
        mock_list_org_members.assert_called_once_with(
            session, "org_123", page=0, per_page=100
        )

    @patch("app.services.organizations_service.list_organization_members")
    def test_list_members_single_member(
        self,
        mock_list_org_members: MagicMock,
        service: OrganizationsService,
        user_token: UserToken,
        session: MagicMock,
    ) -> None:
        """Test listing members with a single member."""
        mock_list_org_members.return_value = (
            [
                {
                    "user_id": "auth0|user1",
                    "email": "alice@example.com",
                    "name": "Alice",
                    "role": "super_admin",
                }
            ],
            1,
        )

        result = service.list_members(user_token, page=0, per_page=100)

        assert len(result.members) == 1
        assert result.members[0].user_id == "auth0|user1"
        assert result.members[0].email == "alice@example.com"
        assert result.members[0].name == "Alice"
        assert result.members[0].picture is None
        assert result.members[0].role == "super_admin"
        assert result.start == 0
        assert result.limit == 100
        assert result.total == 1
        mock_list_org_members.assert_called_once_with(
            session, "org_123", page=0, per_page=100
        )

    @patch("app.services.organizations_service.list_organization_members")
    def test_list_members_multiple_members_sorted(
        self,
        mock_list_org_members: MagicMock,
        service: OrganizationsService,
        user_token: UserToken,
        session: MagicMock,
    ) -> None:
        """Test listing multiple members verifies they are sorted by name."""
        mock_list_org_members.return_value = (
            [
                {
                    "user_id": "auth0|user1",
                    "email": "alice@example.com",
                    "name": "Alice",
                    "role": "super_admin",
                },
                {
                    "user_id": "auth0|user2",
                    "email": "bob@example.com",
                    "name": "Bob",
                    "role": "member",
                },
                {
                    "user_id": "auth0|user3",
                    "email": "charlie@example.com",
                    "name": "Charlie",
                    "role": "member",
                },
            ],
            3,
        )

        result = service.list_members(user_token, page=0, per_page=100)

        assert len(result.members) == 3
        # Verify order is maintained from repository (which sorts by name)
        assert result.members[0].name == "Alice"
        assert result.members[1].name == "Bob"
        assert result.members[2].name == "Charlie"
        assert result.total == 3
        mock_list_org_members.assert_called_once_with(
            session, "org_123", page=0, per_page=100
        )

    @patch("app.services.organizations_service.list_organization_members")
    def test_list_members_pagination_first_page(
        self,
        mock_list_org_members: MagicMock,
        service: OrganizationsService,
        user_token: UserToken,
        session: MagicMock,
    ) -> None:
        """Test pagination on first page."""
        mock_list_org_members.return_value = (
            [
                {
                    "user_id": "auth0|user1",
                    "email": "alice@example.com",
                    "name": "Alice",
                    "role": "super_admin",
                },
                {
                    "user_id": "auth0|user2",
                    "email": "bob@example.com",
                    "name": "Bob",
                    "role": "member",
                },
            ],
            5,  # Total of 5 members in org
        )

        result = service.list_members(user_token, page=0, per_page=2)

        assert len(result.members) == 2
        assert result.start == 0
        assert result.limit == 2
        assert result.total == 5
        mock_list_org_members.assert_called_once_with(
            session, "org_123", page=0, per_page=2
        )

    @patch("app.services.organizations_service.list_organization_members")
    def test_list_members_pagination_second_page(
        self,
        mock_list_org_members: MagicMock,
        service: OrganizationsService,
        user_token: UserToken,
        session: MagicMock,
    ) -> None:
        """Test pagination on second page."""
        mock_list_org_members.return_value = (
            [
                {
                    "user_id": "auth0|user3",
                    "email": "charlie@example.com",
                    "name": "Charlie",
                    "role": "member",
                }
            ],
            5,  # Total of 5 members in org
        )

        result = service.list_members(user_token, page=1, per_page=2)

        assert len(result.members) == 1
        assert result.members[0].name == "Charlie"
        assert result.start == 2  # page 1 * per_page 2
        assert result.limit == 2
        assert result.total == 5
        mock_list_org_members.assert_called_once_with(
            session, "org_123", page=1, per_page=2
        )

    @patch("app.services.organizations_service.list_organization_members")
    def test_list_members_role_format_singular(
        self,
        mock_list_org_members: MagicMock,
        service: OrganizationsService,
        user_token: UserToken,
        session: MagicMock,
    ) -> None:
        """Test that role is returned as singular string value."""
        mock_list_org_members.return_value = (
            [
                {
                    "user_id": "auth0|user1",
                    "email": "alice@example.com",
                    "name": "Alice",
                    "role": "super_admin",
                },
                {
                    "user_id": "auth0|user2",
                    "email": "bob@example.com",
                    "name": "Bob",
                    "role": "member",
                },
            ],
            2,
        )

        result = service.list_members(user_token, page=0, per_page=100)

        # Verify role is a singular string
        assert isinstance(result.members[0].role, str)
        assert result.members[0].role == "super_admin"

        assert isinstance(result.members[1].role, str)
        assert result.members[1].role == "member"

    @patch("app.services.organizations_service.list_organization_members")
    def test_list_members_null_name_handling(
        self,
        mock_list_org_members: MagicMock,
        service: OrganizationsService,
        user_token: UserToken,
        session: MagicMock,
    ) -> None:
        """Test that members with null names are handled correctly."""
        mock_list_org_members.return_value = (
            [
                {
                    "user_id": "auth0|user1",
                    "email": "alice@example.com",
                    "name": "Alice",
                    "role": "super_admin",
                },
                {
                    "user_id": "auth0|user2",
                    "email": "bob@example.com",
                    "name": None,
                    "role": "member",
                },
            ],
            2,
        )

        result = service.list_members(user_token, page=0, per_page=100)

        assert len(result.members) == 2
        assert result.members[0].name == "Alice"
        assert result.members[1].name is None
        assert result.total == 2
