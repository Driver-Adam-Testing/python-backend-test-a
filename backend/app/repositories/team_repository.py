"""Repository functions for Team data access."""

from uuid import UUID

from database.models import PrimaryAssetRoleGrant, Team, TeamMembership
from database.models_enums import TeamRole
from sqlmodel import Session, func, select


def get_team_by_id(
    session: Session,
    team_id: UUID,
    organization_id: str,
) -> Team | None:
    """
    Get a single team by ID.

    Args:
        session: Database session
        team_id: Team ID
        organization_id: Organization ID to verify ownership

    Returns:
        Team or None if not found
    """
    query = select(Team).where(
        Team.id == team_id,
        Team.organization_id == organization_id,
    )
    return session.exec(query).first()


def get_teams_with_counts(
    session: Session,
    organization_id: str,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get teams with aggregated counts of admins, members, and sources.

    Args:
        session: Database session
        organization_id: Organization ID to filter by
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with team data and counts
    """
    admin_count_subq = (
        select(
            TeamMembership.team_id,
            func.count(TeamMembership.id).label("admin_count"),
        )
        .where(TeamMembership.role == TeamRole.team_admin)
        .group_by(TeamMembership.team_id)
        .subquery()
    )

    member_count_subq = (
        select(
            TeamMembership.team_id,
            func.count(TeamMembership.id).label("member_count"),
        )
        .where(TeamMembership.role == TeamRole.team_member)
        .group_by(TeamMembership.team_id)
        .subquery()
    )

    source_count_subq = (
        select(
            PrimaryAssetRoleGrant.team_id,
            func.count(PrimaryAssetRoleGrant.id).label("source_count"),
        )
        .where(PrimaryAssetRoleGrant.team_id.isnot(None))
        .group_by(PrimaryAssetRoleGrant.team_id)
        .subquery()
    )

    query = (
        select(
            Team,
            func.coalesce(admin_count_subq.c.admin_count, 0).label("admins"),
            func.coalesce(member_count_subq.c.member_count, 0).label("members"),
            func.coalesce(source_count_subq.c.source_count, 0).label("sources"),
        )
        .where(Team.organization_id == organization_id)
        .outerjoin(admin_count_subq, Team.id == admin_count_subq.c.team_id)
        .outerjoin(member_count_subq, Team.id == member_count_subq.c.team_id)
        .outerjoin(source_count_subq, Team.id == source_count_subq.c.team_id)
        .order_by(Team.name)
        .offset(offset)
        .limit(limit)
    )

    results = session.exec(query).all()

    return [
        {
            "team": team,
            "admins": admins,
            "members": members,
            "sources": sources,
        }
        for team, admins, members, sources in results
    ]


def get_team_with_counts(
    session: Session,
    team_id: UUID,
    organization_id: str,
) -> dict | None:
    """
    Get a single team with aggregated counts.

    Args:
        session: Database session
        team_id: Team ID
        organization_id: Organization ID to verify ownership

    Returns:
        Dictionary with team data and counts, or None if not found
    """
    admin_count_subq = (
        select(
            TeamMembership.team_id,
            func.count(TeamMembership.id).label("admin_count"),
        )
        .where(TeamMembership.role == TeamRole.team_admin)
        .group_by(TeamMembership.team_id)
        .subquery()
    )

    member_count_subq = (
        select(
            TeamMembership.team_id,
            func.count(TeamMembership.id).label("member_count"),
        )
        .where(TeamMembership.role == TeamRole.team_member)
        .group_by(TeamMembership.team_id)
        .subquery()
    )

    source_count_subq = (
        select(
            PrimaryAssetRoleGrant.team_id,
            func.count(PrimaryAssetRoleGrant.id).label("source_count"),
        )
        .where(PrimaryAssetRoleGrant.team_id.isnot(None))
        .group_by(PrimaryAssetRoleGrant.team_id)
        .subquery()
    )

    query = (
        select(
            Team,
            func.coalesce(admin_count_subq.c.admin_count, 0).label("admins"),
            func.coalesce(member_count_subq.c.member_count, 0).label("members"),
            func.coalesce(source_count_subq.c.source_count, 0).label("sources"),
        )
        .where(Team.id == team_id, Team.organization_id == organization_id)
        .outerjoin(admin_count_subq, Team.id == admin_count_subq.c.team_id)
        .outerjoin(member_count_subq, Team.id == member_count_subq.c.team_id)
        .outerjoin(source_count_subq, Team.id == source_count_subq.c.team_id)
    )

    result = session.exec(query).first()

    if not result:
        return None

    team, admins, members, sources = result
    return {
        "team": team,
        "admins": admins,
        "members": members,
        "sources": sources,
    }


def search_teams_with_counts(
    session: Session,
    organization_id: str,
    query: str,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Search teams by name with aggregated counts.

    Args:
        session: Database session
        organization_id: Organization ID to filter by
        query: Search query (case-insensitive)
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with team data and counts
    """
    admin_count_subq = (
        select(
            TeamMembership.team_id,
            func.count(TeamMembership.id).label("admin_count"),
        )
        .where(TeamMembership.role == TeamRole.team_admin)
        .group_by(TeamMembership.team_id)
        .subquery()
    )

    member_count_subq = (
        select(
            TeamMembership.team_id,
            func.count(TeamMembership.id).label("member_count"),
        )
        .where(TeamMembership.role == TeamRole.team_member)
        .group_by(TeamMembership.team_id)
        .subquery()
    )

    source_count_subq = (
        select(
            PrimaryAssetRoleGrant.team_id,
            func.count(PrimaryAssetRoleGrant.id).label("source_count"),
        )
        .where(PrimaryAssetRoleGrant.team_id.isnot(None))
        .group_by(PrimaryAssetRoleGrant.team_id)
        .subquery()
    )

    search_query = (
        select(
            Team,
            func.coalesce(admin_count_subq.c.admin_count, 0).label("admins"),
            func.coalesce(member_count_subq.c.member_count, 0).label("members"),
            func.coalesce(source_count_subq.c.source_count, 0).label("sources"),
        )
        .where(
            Team.organization_id == organization_id,
            Team.name.ilike(f"%{query}%"),
        )
        .outerjoin(admin_count_subq, Team.id == admin_count_subq.c.team_id)
        .outerjoin(member_count_subq, Team.id == member_count_subq.c.team_id)
        .outerjoin(source_count_subq, Team.id == source_count_subq.c.team_id)
        .order_by(Team.name)
        .offset(offset)
        .limit(limit)
    )

    results = session.exec(search_query).all()

    return [
        {
            "team": team,
            "admins": admins,
            "members": members,
            "sources": sources,
        }
        for team, admins, members, sources in results
    ]


def count_teams(
    session: Session,
    organization_id: str,
) -> int:
    """
    Count total teams in an organization.

    Args:
        session: Database session
        organization_id: Organization ID

    Returns:
        Count of teams
    """
    query = (
        select(func.count())
        .select_from(Team)
        .where(Team.organization_id == organization_id)
    )
    return session.exec(query).one()


def count_teams_by_search(
    session: Session,
    organization_id: str,
    search_query: str,
) -> int:
    """
    Count teams matching a search query.

    Args:
        session: Database session
        organization_id: Organization ID
        search_query: Search query (case-insensitive)

    Returns:
        Count of matching teams
    """
    query = (
        select(func.count())
        .select_from(Team)
        .where(
            Team.organization_id == organization_id,
            Team.name.ilike(f"%{search_query}%"),
        )
    )
    return session.exec(query).one()


def create_team(
    session: Session,
    team: Team,
) -> Team:
    """
    Create a new team.

    Args:
        session: Database session
        team: Team instance to create

    Returns:
        Created team
    """
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def delete_team(
    session: Session,
    team: Team,
) -> None:
    """
    Delete a team.

    Args:
        session: Database session
        team: Team instance to delete
    """
    session.delete(team)
    session.commit()
