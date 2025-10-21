"""Unit tests for TeamMemberService business logic."""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from database.models import Team, TeamMembership, User
from database.models_enums import TeamRole
from fastapi import HTTPException

from app.schemas.team_member_schema import (
    AddTeamMembersRequest,
    RemoveTeamMembersRequest,
    TeamMemberAddInput,
    UpdateTeamMembersRequest,
)
from app.services.team_member_service import (
    TeamMemberService,
    get_user_by_id,
    map_team_role_to_backend,
    map_team_role_to_frontend,
    member_dict_to_response,
)


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def team_member_service(session: MagicMock) -> TeamMemberService:
    """Create a TeamMemberService instance."""
    return TeamMemberService(session)


@pytest.fixture
def org_id() -> str:
    """Return a test organization ID."""
    return "org-123"


@pytest.fixture
def team_id() -> UUID:
    """Return a test team ID."""
    return uuid4()


@pytest.fixture
def user_id() -> str:
    """Return a test user ID."""
    return "user-123"


@pytest.fixture
def sample_team(team_id: UUID, org_id: str) -> Team:
    """Create a sample team."""
    return Team(
        id=team_id,
        organization_id=org_id,
        name="Engineering",
    )


@pytest.fixture
def sample_user(user_id: str) -> User:
    """Create a sample user."""
    return User(
        id=user_id,
        name="John Doe",
        email="john@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_membership(team_id: UUID, user_id: str) -> TeamMembership:
    """Create a sample team membership."""
    return TeamMembership(
        id=uuid4(),
        team_id=team_id,
        user_id=user_id,
        role=TeamRole.member,
    )


@pytest.fixture
def member_dict(
    sample_membership: TeamMembership, sample_user: User, sample_team: Team
) -> dict[str, Any]:
    """Create a member dict with details."""
    return {
        "membership": sample_membership,
        "user": sample_user,
        "team": sample_team,
    }


class TestRoleMappingFunctions:
    """Tests for role mapping utility functions."""

    def test_map_team_role_to_backend_admin(self) -> None:
        """Should map 'admin' to TeamRole.team_admin."""
        result = map_team_role_to_backend("admin")
        assert result == TeamRole.team_admin

    def test_map_team_role_to_backend_member(self) -> None:
        """Should map 'member' to TeamRole.member."""
        result = map_team_role_to_backend("member")
        assert result == TeamRole.member

    def test_map_team_role_to_backend_invalid_raises_error(self) -> None:
        """Should raise ValueError for invalid role."""
        with pytest.raises(ValueError, match="Invalid role"):
            map_team_role_to_backend("invalid")

    def test_map_team_role_to_frontend_admin(self) -> None:
        """Should map TeamRole.team_admin to 'admin'."""
        result = map_team_role_to_frontend(TeamRole.team_admin)
        assert result == "admin"

    def test_map_team_role_to_frontend_member(self) -> None:
        """Should map TeamRole.member to 'member'."""
        result = map_team_role_to_frontend(TeamRole.member)
        assert result == "member"


class TestMemberDictToResponse:
    """Tests for member_dict_to_response function."""

    def test_converts_member_dict_to_response(
        self, member_dict: dict[str, Any], user_id: str, team_id: UUID
    ) -> None:
        """Should convert member dict to TeamMemberResponse."""
        response = member_dict_to_response(member_dict)

        assert response.user_id == user_id
        assert response.name == "John Doe"
        assert response.email == "john@example.com"
        assert response.team_id == str(team_id)
        assert response.team_name == "Engineering"
        assert response.team_role == "member"
        assert response.created_at is not None
        assert response.last_active is not None

    def test_maps_team_admin_to_frontend(self, member_dict: dict[str, Any]) -> None:
        """Should map team_admin role to 'admin' in response."""
        member_dict["membership"].role = TeamRole.team_admin

        response = member_dict_to_response(member_dict)

        assert response.team_role == "admin"


class TestGetUserById:
    """Tests for get_user_by_id helper function."""

    def test_returns_user_when_found(
        self, session: MagicMock, user_id: str, sample_user: User
    ) -> None:
        """Should return user when found."""
        session.exec.return_value.first.return_value = sample_user

        result = get_user_by_id(session, user_id)

        assert result == sample_user

    def test_returns_none_when_not_found(
        self, session: MagicMock, user_id: str
    ) -> None:
        """Should return None when user not found."""
        session.exec.return_value.first.return_value = None

        result = get_user_by_id(session, user_id)

        assert result is None


class TestGetTeamMembers:
    """Tests for get_team_members method."""

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.team_member_repository")
    def test_returns_team_members(
        self,
        mock_member_repo: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
        member_dict: dict[str, Any],
    ) -> None:
        """Should return paginated list of team members."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_member_repo.get_team_members_with_details.return_value = [member_dict]
        mock_member_repo.count_team_members.return_value = 1

        result = team_member_service.get_team_members(team_id, org_id)

        assert len(result.members) == 1
        assert result.total == 1
        assert result.members[0].name == "John Doe"

    @patch("app.services.team_member_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise HTTPException 404 when team not found."""
        mock_team_repo.get_team_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_member_service.get_team_members(team_id, org_id)

        assert exc_info.value.status_code == 404

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.team_member_repository")
    def test_filters_by_roles(
        self,
        mock_member_repo: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should pass role filter to repository."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_member_repo.get_team_members_with_details.return_value = []
        mock_member_repo.count_team_members.return_value = 0

        team_member_service.get_team_members(team_id, org_id, roles=["admin"])

        mock_member_repo.get_team_members_with_details.assert_called_once()
        call_kwargs = mock_member_repo.get_team_members_with_details.call_args[1]
        assert call_kwargs["roles"] == ["admin"]

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.team_member_repository")
    def test_searches_members(
        self,
        mock_member_repo: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should pass search query to repository."""
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_member_repo.get_team_members_with_details.return_value = []
        mock_member_repo.count_team_members.return_value = 0

        team_member_service.get_team_members(team_id, org_id, search="john")

        call_kwargs = mock_member_repo.get_team_members_with_details.call_args[1]
        assert call_kwargs["search"] == "john"


class TestAddTeamMembers:
    """Tests for add_team_members method."""

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.get_user_by_id")
    def test_adds_members_successfully(
        self,
        mock_get_user: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
        sample_user: User,
    ) -> None:
        """Should add members to team successfully."""
        members = [TeamMemberAddInput(userId="user-1", role="admin")]
        request = AddTeamMembersRequest(members=members)
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_get_user.return_value = sample_user

        team_member_service.add_team_members(team_id, org_id, request)

        assert team_member_service.session.add.called
        assert team_member_service.session.commit.called

    @patch("app.services.team_member_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise HTTPException 404 when team not found."""
        members = [TeamMemberAddInput(userId="user-1", role="admin")]
        request = AddTeamMembersRequest(members=members)
        mock_team_repo.get_team_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_member_service.add_team_members(team_id, org_id, request)

        assert exc_info.value.status_code == 404

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.get_user_by_id")
    def test_raises_404_when_user_not_found(
        self,
        mock_get_user: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should raise HTTPException 404 when user not found."""
        members = [TeamMemberAddInput(userId="user-1", role="admin")]
        request = AddTeamMembersRequest(members=members)
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_member_service.add_team_members(team_id, org_id, request)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.get_user_by_id")
    def test_handles_duplicate_member(
        self,
        mock_get_user: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
        sample_user: User,
    ) -> None:
        """Should raise HTTPException 400 when member already exists."""
        from sqlalchemy.exc import IntegrityError

        members = [TeamMemberAddInput(userId="user-1", role="admin")]
        request = AddTeamMembersRequest(members=members)
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_get_user.return_value = sample_user
        team_member_service.session.commit.side_effect = IntegrityError(
            "", "", Exception("duplicate key value violates unique constraint")
        )

        with pytest.raises(HTTPException) as exc_info:
            team_member_service.add_team_members(team_id, org_id, request)

        assert exc_info.value.status_code == 400
        assert "already exist" in exc_info.value.detail.lower()

    @patch("app.services.team_member_service.org_membership_repository")
    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.get_user_by_id")
    def test_raises_403_when_user_not_in_organization(
        self,
        mock_get_user: MagicMock,
        mock_team_repo: MagicMock,
        mock_org_membership_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
        sample_user: User,
    ) -> None:
        """Should raise HTTPException 403 when user not in organization."""
        members = [TeamMemberAddInput(userId="user-external", role="admin")]
        request = AddTeamMembersRequest(members=members)
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_get_user.return_value = sample_user
        # User exists but is not in organization
        mock_org_membership_repo.check_user_in_organization.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            team_member_service.add_team_members(team_id, org_id, request)

        assert exc_info.value.status_code == 403
        assert "not a member of this organization" in exc_info.value.detail


class TestUpdateTeamMembers:
    """Tests for update_team_members method."""

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.team_member_repository")
    def test_updates_member_roles(
        self,
        mock_member_repo: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
        sample_membership: TeamMembership,
    ) -> None:
        """Should update member roles successfully."""
        members = [TeamMemberAddInput(userId="user-1", role="admin")]
        request = UpdateTeamMembersRequest(members=members)
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_member_repo.get_membership.return_value = sample_membership

        team_member_service.update_team_members(team_id, org_id, request)

        assert sample_membership.role == TeamRole.team_admin
        assert team_member_service.session.add.called
        assert team_member_service.session.commit.called

    @patch("app.services.team_member_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise HTTPException 404 when team not found."""
        members = [TeamMemberAddInput(userId="user-1", role="admin")]
        request = UpdateTeamMembersRequest(members=members)
        mock_team_repo.get_team_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_member_service.update_team_members(team_id, org_id, request)

        assert exc_info.value.status_code == 404

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.team_member_repository")
    def test_raises_404_when_member_not_found(
        self,
        mock_member_repo: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should raise HTTPException 404 when member not in team."""
        members = [TeamMemberAddInput(userId="user-1", role="admin")]
        request = UpdateTeamMembersRequest(members=members)
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_member_repo.get_membership.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_member_service.update_team_members(team_id, org_id, request)

        assert exc_info.value.status_code == 404
        assert "not a member" in exc_info.value.detail.lower()


class TestRemoveTeamMembers:
    """Tests for remove_team_members method."""

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.team_member_repository")
    def test_removes_members_successfully(
        self,
        mock_member_repo: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
        sample_membership: TeamMembership,
    ) -> None:
        """Should remove members from team successfully."""
        request = RemoveTeamMembersRequest(userIds=["user-1"])
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_member_repo.get_membership.return_value = sample_membership

        team_member_service.remove_team_members(team_id, org_id, request)

        assert team_member_service.session.delete.called
        assert team_member_service.session.commit.called

    @patch("app.services.team_member_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise HTTPException 404 when team not found."""
        request = RemoveTeamMembersRequest(userIds=["user-1"])
        mock_team_repo.get_team_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_member_service.remove_team_members(team_id, org_id, request)

        assert exc_info.value.status_code == 404

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.team_member_repository")
    def test_silently_skips_non_existent_members(
        self,
        mock_member_repo: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should not fail when removing non-existent members."""
        request = RemoveTeamMembersRequest(userIds=["user-1", "user-2"])
        mock_team_repo.get_team_by_id.return_value = sample_team
        mock_member_repo.get_membership.return_value = None  # Members don't exist

        # Should not raise exception
        team_member_service.remove_team_members(team_id, org_id, request)

        assert team_member_service.session.commit.called

    @patch("app.services.team_member_service.team_repository")
    @patch("app.services.team_member_service.team_member_repository")
    def test_removes_multiple_members(
        self,
        mock_member_repo: MagicMock,
        mock_team_repo: MagicMock,
        team_member_service: TeamMemberService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should remove multiple members in one operation."""
        request = RemoveTeamMembersRequest(userIds=["user-1", "user-2", "user-3"])
        mock_team_repo.get_team_by_id.return_value = sample_team

        # Return a different membership for each call
        memberships = [
            TeamMembership(
                id=uuid4(), team_id=team_id, user_id="user-1", role=TeamRole.member
            ),
            TeamMembership(
                id=uuid4(), team_id=team_id, user_id="user-2", role=TeamRole.member
            ),
            TeamMembership(
                id=uuid4(), team_id=team_id, user_id="user-3", role=TeamRole.member
            ),
        ]
        mock_member_repo.get_membership.side_effect = memberships

        team_member_service.remove_team_members(team_id, org_id, request)

        assert team_member_service.session.delete.call_count == 3
        assert team_member_service.session.commit.called
