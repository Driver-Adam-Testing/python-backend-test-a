"""Repository functions for Team Member data access."""

from uuid import UUID

from database.models import Team, TeamMembership, User
from database.models_enums import TeamRole
from sqlmodel import Session, and_, func, or_, select


def get_team_members_with_details(
    session: Session,
    team_id: UUID,
    organization_id: str,
    roles: list[TeamRole] | None = None,
    search: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get team members with user and team details.

    Args:
        session: Database session
        team_id: Team ID
        organization_id: Organization ID to verify team ownership
        roles: Optional list of roles to filter by
        search: Optional search query for name or email
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with member data
    """
    query = (
        select(TeamMembership, User, Team)
        .join(User, TeamMembership.user_id == User.id)
        .join(Team, TeamMembership.team_id == Team.id)
        .where(
            TeamMembership.team_id == team_id,
            Team.organization_id == organization_id,
        )
    )

    if roles:
        query = query.where(TeamMembership.role.in_(roles))

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )

    query = query.order_by(User.name).offset(offset).limit(limit)

    results = session.exec(query).all()

    return [
        {
            "membership": membership,
            "user": user,
            "team": team,
        }
        for membership, user, team in results
    ]


def count_team_members(
    session: Session,
    team_id: UUID,
    organization_id: str,
    roles: list[TeamRole] | None = None,
    search: str | None = None,
) -> int:
    """
    Count team members with optional filters.

    Args:
        session: Database session
        team_id: Team ID
        organization_id: Organization ID to verify team ownership
        roles: Optional list of roles to filter by
        search: Optional search query for name or email

    Returns:
        Count of matching team members
    """
    query = (
        select(func.count())
        .select_from(TeamMembership)
        .join(User, TeamMembership.user_id == User.id)
        .join(Team, TeamMembership.team_id == Team.id)
        .where(
            TeamMembership.team_id == team_id,
            Team.organization_id == organization_id,
        )
    )

    if roles:
        query = query.where(TeamMembership.role.in_(roles))

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )

    return session.exec(query).one()


def get_membership(
    session: Session,
    team_id: UUID,
    user_id: str,
) -> TeamMembership | None:
    """
    Get a specific team membership.

    Args:
        session: Database session
        team_id: Team ID
        user_id: User ID

    Returns:
        TeamMembership or None if not found
    """
    query = select(TeamMembership).where(
        and_(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_id,
        )
    )
    return session.exec(query).first()


def create_membership(
    session: Session,
    membership: TeamMembership,
) -> TeamMembership:
    """
    Create a new team membership.

    Args:
        session: Database session
        membership: TeamMembership instance to create

    Returns:
        Created membership
    """
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def delete_membership(
    session: Session,
    membership: TeamMembership,
) -> None:
    """
    Delete a team membership.

    Args:
        session: Database session
        membership: TeamMembership instance to delete
    """
    session.delete(membership)
    session.commit()
