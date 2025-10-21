"""Unit tests for TeamService business logic."""

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from database.models import Team
from database.models_enums import TeamRole
from fastapi import HTTPException

from app.schemas.team_schema import (
    CreateTeamRequest,
    TeamMemberInput,
    UpdateTeamRequest,
)
from app.services.team_service import (
    TeamService,
    map_team_role_to_backend,
    map_team_role_to_frontend,
    team_dict_to_response,
)


@pytest.fixture
def session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def team_service(session: MagicMock) -> TeamService:
    """Create a TeamService instance."""
    return TeamService(session)


@pytest.fixture
def org_id() -> str:
    """Return a test organization ID."""
    return "org-123"


@pytest.fixture
def team_id() -> UUID:
    """Return a test team ID."""
    return uuid4()


@pytest.fixture
def sample_team(team_id: UUID, org_id: str) -> Team:
    """Create a sample team."""
    return Team(
        id=team_id,
        organization_id=org_id,
        name="Engineering",
    )


@pytest.fixture
def team_dict_with_counts(sample_team: Team) -> dict[str, Any]:
    """Create a team dict with counts."""
    return {
        "team": sample_team,
        "admins": 2,
        "members": 5,
        "sources": 3,
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


class TestTeamDictToResponse:
    """Tests for team_dict_to_response function."""

    def test_converts_team_with_timestamps(
        self, team_dict_with_counts: dict[str, Any]
    ) -> None:
        """Should convert team dict to TeamResponse with timestamps."""
        response = team_dict_to_response(team_dict_with_counts)

        assert response.id == str(team_dict_with_counts["team"].id)
        assert response.name == "Engineering"
        assert response.admins == 2
        assert response.members == 5
        assert response.sources == 3
        assert response.created_at is not None
        assert response.updated_at is not None

    def test_handles_missing_timestamps(self, team_id: UUID, org_id: str) -> None:
        """Should handle teams without timestamps gracefully."""
        team = Team(id=team_id, organization_id=org_id, name="Test")
        team_dict = {"team": team, "admins": 0, "members": 0, "sources": 0}

        response = team_dict_to_response(team_dict)

        assert response.created_at is not None
        assert response.updated_at is not None


class TestCreateTeam:
    """Tests for create_team method."""

    @patch("app.services.team_service.team_repository")
    def test_creates_team_successfully(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        org_id: str,
        sample_team: Team,
        team_dict_with_counts: dict[str, Any],
    ) -> None:
        """Should create team and return response with counts."""
        request = CreateTeamRequest(name="Engineering")
        mock_repo.create_team.return_value = sample_team
        mock_repo.get_team_with_counts.return_value = team_dict_with_counts

        result = team_service.create_team(org_id, request)

        assert result.name == "Engineering"
        assert result.admins == 2
        assert result.members == 5
        mock_repo.create_team.assert_called_once()
        mock_repo.get_team_with_counts.assert_called_once()

    @patch("app.services.team_service.team_repository")
    def test_creates_team_with_members(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        org_id: str,
        sample_team: Team,
        team_dict_with_counts: dict[str, Any],
    ) -> None:
        """Should create team with initial members."""
        members = [
            TeamMemberInput(userId="user-1", role="admin"),
            TeamMemberInput(userId="user-2", role="member"),
        ]
        request = CreateTeamRequest(name="Engineering", members=members)
        mock_repo.create_team.return_value = sample_team
        mock_repo.get_team_with_counts.return_value = team_dict_with_counts

        result = team_service.create_team(org_id, request)

        assert result.name == "Engineering"
        # Verify members were added (session.add called for memberships)
        assert team_service.session.add.called

    @patch("app.services.team_service.team_repository")
    def test_handles_duplicate_team_name(
        self, mock_repo: MagicMock, team_service: TeamService, org_id: str
    ) -> None:
        """Should raise HTTPException when team name already exists."""
        from sqlalchemy.exc import IntegrityError

        request = CreateTeamRequest(name="Engineering")
        error = IntegrityError(
            "", "", Exception("duplicate key value violates unique constraint")
        )
        mock_repo.create_team.side_effect = error

        with pytest.raises(HTTPException) as exc_info:
            team_service.create_team(org_id, request)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    @patch("app.services.team_service.team_repository")
    def test_strips_team_name(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        org_id: str,
        sample_team: Team,
        team_dict_with_counts: dict[str, Any],
    ) -> None:
        """Should strip whitespace from team name."""
        request = CreateTeamRequest(name="  Engineering  ")
        mock_repo.create_team.return_value = sample_team
        mock_repo.get_team_with_counts.return_value = team_dict_with_counts

        team_service.create_team(org_id, request)

        # Verify create_team was called with stripped name
        call_args = mock_repo.create_team.call_args
        created_team = call_args[0][1]  # Second positional arg (team)
        assert created_team.name == "Engineering"


class TestGetTeams:
    """Tests for get_teams method."""

    @patch("app.services.team_service.team_repository")
    def test_returns_paginated_teams(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        org_id: str,
        team_dict_with_counts: dict[str, Any],
    ) -> None:
        """Should return paginated list of teams."""
        mock_repo.get_teams_with_counts.return_value = [team_dict_with_counts]
        mock_repo.count_teams.return_value = 1

        result = team_service.get_teams(org_id, limit=30, offset=0)

        assert len(result.teams) == 1
        assert result.total == 1
        assert result.teams[0].name == "Engineering"
        mock_repo.get_teams_with_counts.assert_called_once_with(
            session=team_service.session,
            organization_id=org_id,
            limit=30,
            offset=0,
        )

    @patch("app.services.team_service.team_repository")
    def test_respects_pagination_params(
        self, mock_repo: MagicMock, team_service: TeamService, org_id: str
    ) -> None:
        """Should pass pagination parameters to repository."""
        mock_repo.get_teams_with_counts.return_value = []
        mock_repo.count_teams.return_value = 0

        team_service.get_teams(org_id, limit=10, offset=20)

        mock_repo.get_teams_with_counts.assert_called_once_with(
            session=team_service.session,
            organization_id=org_id,
            limit=10,
            offset=20,
        )


class TestGetTeam:
    """Tests for get_team method."""

    @patch("app.services.team_service.team_repository")
    def test_returns_team_when_found(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        team_id: UUID,
        org_id: str,
        team_dict_with_counts: dict[str, Any],
    ) -> None:
        """Should return team when it exists."""
        mock_repo.get_team_with_counts.return_value = team_dict_with_counts

        result = team_service.get_team(team_id, org_id)

        assert result.name == "Engineering"
        assert result.id == str(team_id)

    @patch("app.services.team_service.team_repository")
    def test_raises_404_when_not_found(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise HTTPException 404 when team not found."""
        mock_repo.get_team_with_counts.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_service.get_team(team_id, org_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestUpdateTeam:
    """Tests for update_team method."""

    @patch("app.services.team_service.team_repository")
    def test_updates_team_name(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
        team_dict_with_counts: dict[str, Any],
    ) -> None:
        """Should update team name successfully."""
        request = UpdateTeamRequest(name="Updated Team")
        mock_repo.get_team_by_id.return_value = sample_team
        mock_repo.get_team_with_counts.return_value = team_dict_with_counts

        team_service.update_team(team_id, org_id, request)

        assert team_service.session.add.called
        assert team_service.session.commit.called
        mock_repo.get_team_with_counts.assert_called_once()

    @patch("app.services.team_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise HTTPException 404 when team not found."""
        request = UpdateTeamRequest(name="Updated Team")
        mock_repo.get_team_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_service.update_team(team_id, org_id, request)

        assert exc_info.value.status_code == 404

    @patch("app.services.team_service.team_repository")
    def test_handles_duplicate_name(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should raise HTTPException 400 when name already exists."""
        from sqlalchemy.exc import IntegrityError

        request = UpdateTeamRequest(name="Existing Team")
        mock_repo.get_team_by_id.return_value = sample_team
        team_service.session.commit.side_effect = IntegrityError(
            "", "", Exception("duplicate key value violates unique constraint")
        )

        with pytest.raises(HTTPException) as exc_info:
            team_service.update_team(team_id, org_id, request)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail


class TestDeleteTeam:
    """Tests for delete_team method."""

    @patch("app.services.team_service.team_repository")
    def test_deletes_team_successfully(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should delete team and its associations."""
        mock_repo.get_team_by_id.return_value = sample_team
        mock_query = team_service.session.query.return_value.filter.return_value
        mock_query.all.return_value = []

        team_service.delete_team(team_id, org_id)

        mock_repo.delete_team.assert_called_once_with(team_service.session, sample_team)

    @patch("app.services.team_service.team_repository")
    def test_raises_404_when_team_not_found(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        team_id: UUID,
        org_id: str,
    ) -> None:
        """Should raise HTTPException 404 when team not found."""
        mock_repo.get_team_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            team_service.delete_team(team_id, org_id)

        assert exc_info.value.status_code == 404

    @patch("app.services.team_service.team_repository")
    def test_deletes_source_grants(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        team_id: UUID,
        org_id: str,
        sample_team: Team,
    ) -> None:
        """Should delete associated source grants."""
        mock_repo.get_team_by_id.return_value = sample_team
        mock_grants = [MagicMock(), MagicMock()]
        team_service.session.query.return_value.filter.return_value.all.return_value = (
            mock_grants
        )

        team_service.delete_team(team_id, org_id)

        # Verify grants were deleted
        assert team_service.session.delete.call_count == 2


class TestSearchTeams:
    """Tests for search_teams method."""

    @patch("app.services.team_service.team_repository")
    def test_searches_teams_by_query(
        self,
        mock_repo: MagicMock,
        team_service: TeamService,
        org_id: str,
        team_dict_with_counts: dict[str, Any],
    ) -> None:
        """Should search teams and return results."""
        mock_repo.search_teams_with_counts.return_value = [team_dict_with_counts]
        mock_repo.count_teams_by_search.return_value = 1

        result = team_service.search_teams(org_id, "eng", limit=30, offset=0)

        assert len(result.teams) == 1
        assert result.total == 1
        mock_repo.search_teams_with_counts.assert_called_once_with(
            session=team_service.session,
            organization_id=org_id,
            query="eng",
            limit=30,
            offset=0,
        )

    @patch("app.services.team_service.team_repository")
    def test_returns_empty_when_no_matches(
        self, mock_repo: MagicMock, team_service: TeamService, org_id: str
    ) -> None:
        """Should return empty list when no matches found."""
        mock_repo.search_teams_with_counts.return_value = []
        mock_repo.count_teams_by_search.return_value = 0

        result = team_service.search_teams(org_id, "nonexistent")

        assert len(result.teams) == 0
        assert result.total == 0
