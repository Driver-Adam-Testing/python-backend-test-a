"""Unit tests for members_search API routes."""

from unittest.mock import MagicMock, patch

import pytest

from app.api.routes.v1 import members_search
from app.schemas.rbac_search_schema import MemberSearchItem, MemberSearchResponse


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def user() -> MagicMock:
    """Create a mock user token."""
    user = MagicMock()
    user.user_id = "user-123"
    user.organization_id = "org-123"
    return user


class TestSearchMembers:
    """Tests for search_members endpoint."""

    @patch("app.api.routes.v1.members_search.RBACSearchService")
    def test_returns_search_results(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should return combined user and team search results."""
        mock_service = mock_service_class.return_value
        mock_service.search_members.return_value = MemberSearchResponse(
            items=[
                MemberSearchItem(
                    member_id="user-456",
                    kind="user",
                    name="John Doe",
                    email="john@example.com",
                    picture="",
                ),
                MemberSearchItem(
                    member_id="team-789",
                    kind="team",
                    name="Engineering Team",
                    email=None,
                    picture=None,
                ),
            ],
            total=2,
        )

        response = members_search.search_members(
            session=session,
            user=user,
            query="test",
            limit=30,
            offset=0,
        )

        assert isinstance(response, MemberSearchResponse)
        assert len(response.items) == 2
        assert response.total == 2
        assert response.items[0].kind == "user"
        assert response.items[1].kind == "team"

    @patch("app.api.routes.v1.members_search.RBACSearchService")
    def test_passes_correct_parameters_to_service(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should pass correct parameters to service method."""
        mock_service = mock_service_class.return_value
        mock_service.search_members.return_value = MemberSearchResponse(
            items=[],
            total=0,
        )

        members_search.search_members(
            session=session,
            user=user,
            query="john",
            limit=50,
            offset=10,
        )

        mock_service.search_members.assert_called_once_with(
            organization_id="org-123",
            query="john",
            limit=50,
            offset=10,
        )

    @patch("app.api.routes.v1.members_search.RBACSearchService")
    def test_uses_default_pagination_values(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should use default values for limit and offset."""
        mock_service = mock_service_class.return_value
        mock_service.search_members.return_value = MemberSearchResponse(
            items=[],
            total=0,
        )

        members_search.search_members(
            session=session,
            user=user,
            query="test",
            limit=30,
            offset=0,
        )

        mock_service.search_members.assert_called_once_with(
            organization_id="org-123",
            query="test",
            limit=30,
            offset=0,
        )

    @patch("app.api.routes.v1.members_search.RBACSearchService")
    def test_returns_empty_when_no_matches(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should return empty list when no matches found."""
        mock_service = mock_service_class.return_value
        mock_service.search_members.return_value = MemberSearchResponse(
            items=[],
            total=0,
        )

        response = members_search.search_members(
            session=session,
            user=user,
            query="nonexistent",
            limit=30,
            offset=0,
        )

        assert len(response.items) == 0
        assert response.total == 0

    @patch("app.api.routes.v1.members_search.RBACSearchService")
    def test_user_items_have_email_and_picture(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should return user items with email and picture fields."""
        mock_service = mock_service_class.return_value
        mock_service.search_members.return_value = MemberSearchResponse(
            items=[
                MemberSearchItem(
                    member_id="user-456",
                    kind="user",
                    name="John Doe",
                    email="john@example.com",
                    picture="https://example.com/picture.jpg",
                ),
            ],
            total=1,
        )

        response = members_search.search_members(
            session=session,
            user=user,
            query="john",
            limit=30,
            offset=0,
        )

        assert len(response.items) == 1
        user_item = response.items[0]
        assert user_item.kind == "user"
        assert user_item.email == "john@example.com"
        assert user_item.picture == "https://example.com/picture.jpg"

    @patch("app.api.routes.v1.members_search.RBACSearchService")
    def test_team_items_have_null_email_and_picture(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
    ) -> None:
        """Should return team items with null email and picture fields."""
        mock_service = mock_service_class.return_value
        mock_service.search_members.return_value = MemberSearchResponse(
            items=[
                MemberSearchItem(
                    member_id="team-789",
                    kind="team",
                    name="Engineering Team",
                    email=None,
                    picture=None,
                ),
            ],
            total=1,
        )

        response = members_search.search_members(
            session=session,
            user=user,
            query="eng",
            limit=30,
            offset=0,
        )

        assert len(response.items) == 1
        team_item = response.items[0]
        assert team_item.kind == "team"
        assert team_item.email is None
        assert team_item.picture is None
