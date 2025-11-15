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
    user_id: str | None = None,
) -> list[dict]:
    """
    If user_id is provided, only returns teams where the user is a member.
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

    if user_id:
        query = query.where(
            Team.id.in_(
                select(TeamMembership.team_id).where(TeamMembership.user_id == user_id)
            )
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
    """Returns dict with 'team', 'admins', 'members', 'sources' keys, or None if not found."""
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
    user_id: str | None = None,
) -> list[dict]:
    """
    If user_id is provided, only returns teams where the user is a member.
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

    if user_id:
        search_query = search_query.where(
            Team.id.in_(
                select(TeamMembership.team_id).where(TeamMembership.user_id == user_id)
            )
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
    user_id: str | None = None,
) -> int:
    """
    If user_id is provided, only counts teams where the user is a member.
    """
    if user_id:
        query = (
            select(func.count())
            .select_from(Team)
            .join(TeamMembership, Team.id == TeamMembership.team_id)
            .where(
                Team.organization_id == organization_id,
                TeamMembership.user_id == user_id,
            )
        )
    else:
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
    user_id: str | None = None,
) -> int:
    if user_id:
        query = (
            select(func.count())
            .select_from(Team)
            .join(TeamMembership, Team.id == TeamMembership.team_id)
            .where(
                Team.organization_id == organization_id,
                Team.name.ilike(f"%{search_query}%"),
                TeamMembership.user_id == user_id,
            )
        )
    else:
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
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def delete_team(
    session: Session,
    team: Team,
) -> None:
    session.delete(team)
    session.commit()


def get_user_team_role(
    session: Session,
    team_id: UUID,
    user_id: str,
    organization_id: str,
) -> TeamRole | None:
    """Get user's role in a specific team. Returns None if user is not a member."""
    query = (
        select(TeamMembership.role)
        .join(Team, Team.id == TeamMembership.team_id)
        .where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_id,
            Team.organization_id == organization_id,
        )
    )
    return session.exec(query).first()
