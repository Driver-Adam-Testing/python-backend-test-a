"""Repository functions for ACL (PrimaryAssetRoleGrant) data access."""

from uuid import UUID

from database.models import (
    OrgMembership,
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Team,
    TeamMembership,
    User,
)
from database.models_enums import PrimaryAssetRole, PrincipalKind
from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select


def get_grant_by_team_and_asset(
    session: Session,
    team_id: UUID,
    primary_asset_id: UUID,
) -> PrimaryAssetRoleGrant | None:
    """
    Get ACL grant for a specific team and asset.

    Args:
        session: Database session
        team_id: Team ID
        primary_asset_id: Primary asset (source) ID

    Returns:
        Grant or None if not found
    """
    query = select(PrimaryAssetRoleGrant).where(
        PrimaryAssetRoleGrant.team_id == team_id,
        PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
    )
    return session.exec(query).first()


def get_grant_by_user_and_asset(
    session: Session,
    user_id: str,
    primary_asset_id: UUID,
) -> PrimaryAssetRoleGrant | None:
    """
    Get ACL grant for a specific user and asset.

    Args:
        session: Database session
        user_id: User ID
        primary_asset_id: Primary asset (source) ID

    Returns:
        Grant or None if not found
    """
    query = select(PrimaryAssetRoleGrant).where(
        PrimaryAssetRoleGrant.user_id == user_id,
        PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
    )
    return session.exec(query).first()


def get_team_sources_with_details(
    session: Session,
    team_id: UUID,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    visibilities: list[str] | None = None,
    search: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get sources for a team with full PrimaryAsset details.

    Args:
        session: Database session
        team_id: Team ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by (admin, member)
        visibilities: Optional list of visibilities to filter by
        search: Optional search query for display name
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with 'grant' and 'asset' keys
    """

    query = (
        select(PrimaryAssetRoleGrant, PrimaryAsset)
        .join(PrimaryAsset, PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id)
        .options(selectinload(PrimaryAsset.most_recent_version))
        .where(
            PrimaryAssetRoleGrant.team_id == team_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
        )
    )

    # Filter by roles
    if roles:
        query = query.where(PrimaryAssetRoleGrant.role.in_(roles))

    # TODO: Add visibility filtering once visibility field is added to PrimaryAssetRoleGrant

    # Search by display name
    if search:
        query = query.where(PrimaryAsset.display_name.ilike(f"%{search}%"))

    query = query.order_by(PrimaryAsset.display_name).offset(offset).limit(limit)

    results = session.exec(query).all()

    return [{"grant": grant, "asset": asset} for grant, asset in results]


def count_team_sources(
    session: Session,
    team_id: UUID,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    visibilities: list[str] | None = None,
    search: str | None = None,
) -> int:
    """
    Count sources for a team with optional filtering.

    Args:
        session: Database session
        team_id: Team ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        visibilities: Optional list of visibilities to filter by
        search: Optional search query

    Returns:
        Count of matching sources
    """
    query = (
        select(func.count())
        .select_from(PrimaryAssetRoleGrant)
        .join(PrimaryAsset, PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id)
        .where(
            PrimaryAssetRoleGrant.team_id == team_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
        )
    )

    if roles:
        query = query.where(PrimaryAssetRoleGrant.role.in_(roles))

    # TODO: Add visibility filtering once visibility field is added

    if search:
        query = query.where(PrimaryAsset.display_name.ilike(f"%{search}%"))

    return session.exec(query).one()


def get_source_users_with_details(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    user_kind: str | None = None,
    search: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get users (users and teams) for a source with full details.

    When user_kind='user', returns all users with access including:
    - Users with direct grants to the source
    - Users who are members of teams that have grants to the source

    Args:
        session: Database session
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        user_kind: Optional user kind filter ('user' or 'team')
        search: Optional search query for name or email
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with 'grant', 'asset', and 'member' (User or Team) keys
    """
    output = []
    asset = session.exec(
        select(PrimaryAsset).where(PrimaryAsset.id == primary_asset_id)
    ).first()

    if not asset:
        return []

    # Handle user_kind='team' - only return teams
    if user_kind == "team":
        query = select(PrimaryAssetRoleGrant).where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
        )

        if roles:
            query = query.where(PrimaryAssetRoleGrant.role.in_(roles))

        team_grants = session.exec(query).all()

        for grant in team_grants:
            if grant.team_id:
                team = session.exec(
                    select(Team).where(Team.id == grant.team_id)
                ).first()
                if team:
                    if search and search.lower() not in team.name.lower():
                        continue
                    output.append(
                        {"grant": grant, "asset": asset, "kind": "team", "member": team}
                    )

        return output[offset : offset + limit]

    # Handle user_kind='user' or None - return users with direct + team-based access
    users_dict = {}  # user_id -> {grant, user}

    # 1. Get users with direct grants
    direct_user_query = select(PrimaryAssetRoleGrant).where(
        PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
        PrimaryAssetRoleGrant.organization_id == organization_id,
        PrimaryAssetRoleGrant.principal_kind == PrincipalKind.user,
    )

    if roles:
        direct_user_query = direct_user_query.where(
            PrimaryAssetRoleGrant.role.in_(roles)
        )

    direct_grants = session.exec(direct_user_query).all()

    for grant in direct_grants:
        if grant.user_id:
            user = session.exec(select(User).where(User.id == grant.user_id)).first()
            if user:
                users_dict[grant.user_id] = {"grant": grant, "user": user}

    # 2. Get users from teams that have access to the source
    # Get team grants
    team_query = select(PrimaryAssetRoleGrant).where(
        PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
        PrimaryAssetRoleGrant.organization_id == organization_id,
        PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
    )

    if roles:
        team_query = team_query.where(PrimaryAssetRoleGrant.role.in_(roles))

    team_grants = session.exec(team_query).all()

    # For each team, get all members
    for team_grant in team_grants:
        if team_grant.team_id:
            # Get team members
            team_members_query = (
                select(TeamMembership, User)
                .join(User, TeamMembership.user_id == User.id)
                .where(TeamMembership.team_id == team_grant.team_id)
            )
            team_members = session.exec(team_members_query).all()

            for _membership, user in team_members:
                # Only add if not already in dict (direct grants take precedence)
                if user.id not in users_dict:
                    users_dict[user.id] = {"grant": team_grant, "user": user}

    # Convert dict to list and apply search filter
    for data in users_dict.values():
        user = data["user"]
        grant = data["grant"]

        # Apply search filter
        if search and (
            search.lower() not in (user.name or "").lower()
            and search.lower() not in (user.email or "").lower()
        ):
            continue

        output.append({"grant": grant, "asset": asset, "kind": "user", "member": user})

    # Sort by user name for consistent ordering
    output.sort(key=lambda x: (x["member"].name or "").lower())

    # Apply pagination
    return output[offset : offset + limit]


def count_source_users(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    user_kind: str | None = None,
    search: str | None = None,
) -> int:
    """
    Count users for a source with optional filtering.

    Args:
        session: Database session
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        user_kind: Optional user kind filter
        search: Optional search query

    Returns:
        Count of matching users
    """
    # Use the same logic as get_source_users_with_details but just count
    results = get_source_users_with_details(
        session=session,
        primary_asset_id=primary_asset_id,
        organization_id=organization_id,
        roles=roles,
        user_kind=user_kind,
        search=search,
        limit=999999,  # Get all for counting
        offset=0,
    )
    return len(results)


def create_grant(
    session: Session,
    grant: PrimaryAssetRoleGrant,
) -> PrimaryAssetRoleGrant:
    """
    Create a new ACL grant.

    Args:
        session: Database session
        grant: Grant instance to create

    Returns:
        Created grant
    """
    session.add(grant)
    session.commit()
    session.refresh(grant)
    return grant


def delete_grant(
    session: Session,
    grant: PrimaryAssetRoleGrant,
) -> None:
    """
    Delete an ACL grant.

    Args:
        session: Database session
        grant: Grant instance to delete
    """
    session.delete(grant)
    session.commit()


def get_primary_asset_by_id(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
) -> PrimaryAsset | None:
    """
    Get a primary asset by ID.

    Args:
        session: Database session
        primary_asset_id: Primary asset ID
        organization_id: Organization ID to verify ownership

    Returns:
        PrimaryAsset or None if not found
    """
    query = select(PrimaryAsset).where(
        PrimaryAsset.id == primary_asset_id,
        PrimaryAsset.organization_id == organization_id,
    )
    return session.exec(query).first()


def get_user_org_membership(
    session: Session,
    user_id: str,
    organization_id: str,
) -> OrgMembership | None:
    """
    Get a user's organization membership.

    Args:
        session: Database session
        user_id: User ID
        organization_id: Organization ID

    Returns:
        OrgMembership or None if not found
    """
    query = select(OrgMembership).where(
        OrgMembership.user_id == user_id,
        OrgMembership.org_id == organization_id,
    )
    return session.exec(query).first()


def get_user_team_memberships(
    session: Session,
    user_id: str,
    organization_id: str,
) -> list[dict]:
    """
    Get all team memberships for a user in an organization.

    Args:
        session: Database session
        user_id: User ID
        organization_id: Organization ID

    Returns:
        List of dictionaries with 'team' and 'membership' keys
    """
    query = (
        select(TeamMembership, Team)
        .join(Team, TeamMembership.team_id == Team.id)
        .where(
            TeamMembership.user_id == user_id,
            Team.organization_id == organization_id,
        )
        .order_by(Team.name)
    )

    results = session.exec(query).all()
    return [{"membership": membership, "team": team} for membership, team in results]
