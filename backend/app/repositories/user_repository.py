"""Repository functions for User data access."""

from uuid import UUID

from database.models import (
    OrgMembership,
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Team,
    TeamMembership,
    User,
)
from database.models_enums import OrgRole, PrimaryAssetRole, TeamRole
from sqlmodel import Session, func, or_, select


def search_organization_users(
    session: Session,
    organization_id: str,
    query: str,
    limit: int = 30,
    offset: int = 0,
) -> list[User]:
    """
    Search for users within an organization by name or email.

    Args:
        session: Database session
        organization_id: Organization ID
        query: Search query (case-insensitive)
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of matching users
    """
    search_pattern = f"%{query}%"
    search_query = (
        select(User)
        .join(OrgMembership, User.id == OrgMembership.user_id)
        .where(
            OrgMembership.org_id == organization_id,
            or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            ),
        )
        .order_by(User.name)
        .offset(offset)
        .limit(limit)
    )

    return list(session.exec(search_query).all())


def count_organization_users(
    session: Session,
    organization_id: str,
    query: str,
) -> int:
    """
    Count users matching search query in an organization.

    Args:
        session: Database session
        organization_id: Organization ID
        query: Search query (case-insensitive)

    Returns:
        Count of matching users
    """
    search_pattern = f"%{query}%"
    count_query = (
        select(func.count())
        .select_from(User)
        .join(OrgMembership, User.id == OrgMembership.user_id)
        .where(
            OrgMembership.org_id == organization_id,
            or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            ),
        )
    )

    return session.exec(count_query).one()


def get_user_teams_with_details(
    session: Session,
    user_id: str,
    organization_id: str,
    roles: list[TeamRole] | None = None,
    search: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get teams for a user with full team details and aggregated counts.

    Args:
        session: Database session
        user_id: User ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by (admin, member)
        search: Optional search query for team name
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with 'membership', 'team', 'admins', 'members', 'sources'
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
            TeamMembership,
            Team,
            func.coalesce(admin_count_subq.c.admin_count, 0).label("admins"),
            func.coalesce(member_count_subq.c.member_count, 0).label("members"),
            func.coalesce(source_count_subq.c.source_count, 0).label("sources"),
        )
        .join(Team, TeamMembership.team_id == Team.id)
        .where(
            TeamMembership.user_id == user_id,
            Team.organization_id == organization_id,
        )
        .outerjoin(admin_count_subq, Team.id == admin_count_subq.c.team_id)
        .outerjoin(member_count_subq, Team.id == member_count_subq.c.team_id)
        .outerjoin(source_count_subq, Team.id == source_count_subq.c.team_id)
    )

    if roles:
        query = query.where(TeamMembership.role.in_(roles))

    if search:
        query = query.where(Team.name.ilike(f"%{search}%"))

    query = query.order_by(Team.name).offset(offset).limit(limit)

    results = session.exec(query).all()

    return [
        {
            "membership": membership,
            "team": team,
            "admins": admins,
            "members": members,
            "sources": sources,
        }
        for membership, team, admins, members, sources in results
    ]


def count_user_teams(
    session: Session,
    user_id: str,
    organization_id: str,
    roles: list[TeamRole] | None = None,
    search: str | None = None,
) -> int:
    """
    Count teams for a user with optional filtering.

    Args:
        session: Database session
        user_id: User ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        search: Optional search query for team name

    Returns:
        Count of matching teams
    """
    query = (
        select(func.count())
        .select_from(TeamMembership)
        .join(Team, TeamMembership.team_id == Team.id)
        .where(
            TeamMembership.user_id == user_id,
            Team.organization_id == organization_id,
        )
    )

    if roles:
        query = query.where(TeamMembership.role.in_(roles))

    if search:
        query = query.where(Team.name.ilike(f"%{search}%"))

    return session.exec(query).one()


def get_user_team_membership(
    session: Session,
    user_id: str,
    team_id: UUID,
) -> TeamMembership | None:
    """
    Get a specific user's team membership.

    Args:
        session: Database session
        user_id: User ID
        team_id: Team ID

    Returns:
        TeamMembership or None if not found
    """
    query = select(TeamMembership).where(
        TeamMembership.user_id == user_id,
        TeamMembership.team_id == team_id,
    )
    return session.exec(query).first()


def create_user_team_membership(
    session: Session,
    membership: TeamMembership,
) -> TeamMembership:
    """
    Create a new user team membership.

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


def delete_user_team_membership(
    session: Session,
    membership: TeamMembership,
) -> None:
    """
    Delete a user team membership.

    Args:
        session: Database session
        membership: TeamMembership instance to delete
    """
    session.delete(membership)
    session.commit()


def get_user_sources_with_details(
    session: Session,
    user_id: str,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    search: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get sources for a user with full PrimaryAsset details.

    Args:
        session: Database session
        user_id: User ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by (admin, member)
        search: Optional search query for display name
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with 'grant' and 'asset' keys
    """
    from sqlalchemy.orm import selectinload

    # Subquery to get all team IDs that the user is a member of
    user_teams_subq = (
        select(TeamMembership.team_id)
        .where(TeamMembership.user_id == user_id)
        .subquery()
    )

    # Query for grants - include both direct user grants and team grants
    query = (
        select(PrimaryAssetRoleGrant, PrimaryAsset)
        .join(PrimaryAsset, PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id)
        .options(selectinload(PrimaryAsset.most_recent_version))
        .where(
            PrimaryAssetRoleGrant.organization_id == organization_id,
            or_(
                # Direct user grants
                PrimaryAssetRoleGrant.user_id == user_id,
                # Team grants where user is a member
                PrimaryAssetRoleGrant.team_id.in_(select(user_teams_subq)),
            ),
        )
    )

    if roles:
        query = query.where(PrimaryAssetRoleGrant.role.in_(roles))

    if search:
        query = query.where(PrimaryAsset.display_name.ilike(f"%{search}%"))

    query = query.order_by(PrimaryAsset.display_name).offset(offset).limit(limit)

    results = session.exec(query).all()

    return [{"grant": grant, "asset": asset} for grant, asset in results]


def count_user_sources(
    session: Session,
    user_id: str,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    search: str | None = None,
) -> int:
    """
    Count sources for a user with optional filtering.

    Args:
        session: Database session
        user_id: User ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        search: Optional search query

    Returns:
        Count of matching sources
    """
    # Subquery to get all team IDs that the user is a member of
    user_teams_subq = (
        select(TeamMembership.team_id)
        .where(TeamMembership.user_id == user_id)
        .subquery()
    )

    query = (
        select(func.count())
        .select_from(PrimaryAssetRoleGrant)
        .join(PrimaryAsset, PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id)
        .where(
            PrimaryAssetRoleGrant.organization_id == organization_id,
            or_(
                # Direct user grants
                PrimaryAssetRoleGrant.user_id == user_id,
                # Team grants where user is a member
                PrimaryAssetRoleGrant.team_id.in_(select(user_teams_subq)),
            ),
        )
    )

    if roles:
        query = query.where(PrimaryAssetRoleGrant.role.in_(roles))

    if search:
        query = query.where(PrimaryAsset.display_name.ilike(f"%{search}%"))

    return session.exec(query).one()


def get_user_source_grant(
    session: Session,
    user_id: str,
    primary_asset_id: UUID,
) -> PrimaryAssetRoleGrant | None:
    """
    Get a specific user's source grant.

    Args:
        session: Database session
        user_id: User ID
        primary_asset_id: Primary asset (source) ID

    Returns:
        PrimaryAssetRoleGrant or None if not found
    """
    query = select(PrimaryAssetRoleGrant).where(
        PrimaryAssetRoleGrant.user_id == user_id,
        PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
    )
    return session.exec(query).first()


def create_user_source_grant(
    session: Session,
    grant: PrimaryAssetRoleGrant,
) -> PrimaryAssetRoleGrant:
    """
    Create a new user source grant.

    Args:
        session: Database session
        grant: PrimaryAssetRoleGrant instance to create

    Returns:
        Created grant
    """
    session.add(grant)
    session.commit()
    session.refresh(grant)
    return grant


def delete_user_source_grant(
    session: Session,
    grant: PrimaryAssetRoleGrant,
) -> None:
    """
    Delete a user source grant.

    Args:
        session: Database session
        grant: PrimaryAssetRoleGrant instance to delete
    """
    session.delete(grant)
    session.commit()


def get_organization_membership(
    session: Session,
    user_id: str,
    organization_id: str,
) -> OrgMembership | None:
    """
    Get a user's organization membership.

    Args:
        session: Database session
        user_id: User ID (Auth0 user ID)
        organization_id: Organization ID

    Returns:
        OrgMembership or None if not found
    """
    query = select(OrgMembership).where(
        OrgMembership.user_id == user_id,
        OrgMembership.org_id == organization_id,
    )
    return session.exec(query).first()


def update_organization_role(
    session: Session,
    user_id: str,
    organization_id: str,
    new_role: OrgRole,
) -> OrgMembership:
    """
    Update a user's organization role.

    Args:
        session: Database session
        user_id: User ID (Auth0 user ID)
        organization_id: Organization ID
        new_role: New role enum value

    Returns:
        Updated OrgMembership

    Raises:
        ValueError: If membership not found
    """
    # Get membership
    membership = get_organization_membership(session, user_id, organization_id)
    if not membership:
        raise ValueError(
            f"User {user_id} is not a member of organization {organization_id}"
        )

    # Update role
    membership.role = new_role
    session.add(membership)
    session.commit()
    session.refresh(membership)

    return membership


def count_organization_super_admins(
    session: Session,
    organization_id: str,
) -> int:
    """
    Count the number of super_admin users in an organization.

    Args:
        session: Database session
        organization_id: Organization ID

    Returns:
        Count of super_admin users
    """
    from database.models_enums import OrgRole

    query = (
        select(func.count())
        .select_from(OrgMembership)
        .where(
            OrgMembership.org_id == organization_id,
            OrgMembership.role == OrgRole.org_super_admin,
        )
    )
    return session.exec(query).one()


def delete_organization_membership(
    session: Session,
    membership: OrgMembership,
) -> None:
    """
    Delete a user's organization membership.

    Args:
        session: Database session
        membership: OrgMembership instance to delete
    """
    session.delete(membership)
    session.commit()
