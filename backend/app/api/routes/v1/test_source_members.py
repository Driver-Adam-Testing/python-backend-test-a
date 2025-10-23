"""Unit tests for source_members API routes."""

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.api.routes.v1 import source_members
from app.schemas.source_access_schema import (
    AddSourceMembersRequest,
    RemoveSourceMembersRequest,
    SourceMemberInput,
    SourceMemberResponse,
    SourceMembersResponse,
    UpdateSourceMembersRequest,
)


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


@pytest.fixture
def source_id() -> UUID:
    """Return a test source ID."""
    return uuid4()


@pytest.fixture
def member_id() -> str:
    """Return a test member ID."""
    return "member-456"


class TestGetSourceMembers:
    """Tests for get_source_members endpoint."""

    @patch("app.api.routes.v1.source_members.SourceAccessService")
    def test_returns_source_members(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        source_id: UUID,
        member_id: str,
    ) -> None:
        """Should return source members successfully."""
        mock_service = mock_service_class.return_value
        mock_service.get_source_members.return_value = SourceMembersResponse(
            members=[
                SourceMemberResponse(
                    member_id=member_id,
                    kind="user",
                    name="John Doe",
                    email="john@example.com",
                    picture=None,
                    source_id=str(source_id),
                    source_name="Test Repo",
                    source_role="admin",
                    visibility="private",
                    created_at="2025-01-01T00:00:00",
                )
            ],
            total=1,
        )

        response = source_members.get_source_members(
            session=session,
            user=user,
            source_id=source_id,
            limit=30,
            offset=0,
        )

        assert response.total == 1
        assert len(response.members) == 1
        mock_service.get_source_members.assert_called_once()

    @patch("app.api.routes.v1.source_members.SourceAccessService")
    def test_handles_filters(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        source_id: UUID,
    ) -> None:
        """Should pass filters to service."""
        mock_service = mock_service_class.return_value
        mock_service.get_source_members.return_value = SourceMembersResponse(
            members=[], total=0
        )

        source_members.get_source_members(
            session=session,
            user=user,
            source_id=source_id,
            limit=30,
            offset=0,
            roles=["admin"],
            member_kind="user",
            search="john",
        )

        mock_service.get_source_members.assert_called_once_with(
            source_id=source_id,
            organization_id=user.organization_id,
            roles=["admin"],
            member_kind="user",
            search="john",
            limit=30,
            offset=0,
        )


class TestAddSourceMembers:
    """Tests for add_source_members endpoint."""

    @patch("app.api.routes.v1.source_members.SourceAccessService")
    def test_adds_members_successfully(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        source_id: UUID,
        member_id: str,
    ) -> None:
        """Should add members to source successfully."""
        mock_service = mock_service_class.return_value

        request = AddSourceMembersRequest(
            members=[SourceMemberInput(member_id=member_id, kind="user", role="admin")]
        )

        result = source_members.add_source_members(
            session=session,
            user=user,
            source_id=source_id,
            request=request,
        )

        assert result is None
        mock_service.add_source_members.assert_called_once_with(
            source_id=source_id,
            organization_id=user.organization_id,
            request=request,
        )


class TestUpdateSourceMembers:
    """Tests for update_source_members endpoint."""

    @patch("app.api.routes.v1.source_members.SourceAccessService")
    def test_updates_members_successfully(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        source_id: UUID,
        member_id: str,
    ) -> None:
        """Should update member roles successfully."""
        mock_service = mock_service_class.return_value

        request = UpdateSourceMembersRequest(
            members=[SourceMemberInput(member_id=member_id, kind="user", role="member")]
        )

        result = source_members.update_source_members(
            session=session,
            user=user,
            source_id=source_id,
            request=request,
        )

        assert result is None
        mock_service.update_source_members.assert_called_once_with(
            source_id=source_id,
            organization_id=user.organization_id,
            request=request,
        )


class TestRemoveSourceMembers:
    """Tests for remove_source_members endpoint."""

    @patch("app.api.routes.v1.source_members.SourceAccessService")
    def test_removes_members_successfully(
        self,
        mock_service_class: MagicMock,
        session: MagicMock,
        user: MagicMock,
        source_id: UUID,
        member_id: str,
    ) -> None:
        """Should remove members from source successfully."""
        mock_service = mock_service_class.return_value

        request = RemoveSourceMembersRequest(
            members=[{"member_id": member_id, "kind": "user"}]
        )

        result = source_members.remove_source_members(
            session=session,
            user=user,
            source_id=source_id,
            request=request,
        )

        assert result is None
        mock_service.remove_source_members.assert_called_once_with(
            source_id=source_id,
            organization_id=user.organization_id,
            request=request,
        )
