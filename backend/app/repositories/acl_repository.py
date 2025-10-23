"""Repository functions for ACL (PrimaryAssetRoleGrant) data access."""

from uuid import UUID

from database.models import PrimaryAsset, PrimaryAssetRoleGrant, Team, User
from database.models_enums import PrimaryAssetRole, PrincipalKind
from sqlmodel import Session, func, or_, select


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
    roles: list[str] | None = None,
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
        .where(
            PrimaryAssetRoleGrant.team_id == team_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
        )
    )

    # Filter by roles
    if roles:
        backend_roles = [
            PrimaryAssetRole.admin if r == "admin" else PrimaryAssetRole.viewer
            for r in roles
        ]
        query = query.where(PrimaryAssetRoleGrant.role.in_(backend_roles))

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
    roles: list[str] | None = None,
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
        backend_roles = [
            PrimaryAssetRole.admin if r == "admin" else PrimaryAssetRole.viewer
            for r in roles
        ]
        query = query.where(PrimaryAssetRoleGrant.role.in_(backend_roles))

    # TODO: Add visibility filtering once visibility field is added

    if search:
        query = query.where(PrimaryAsset.display_name.ilike(f"%{search}%"))

    return session.exec(query).one()


def get_source_members_with_details(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    roles: list[str] | None = None,
    member_kind: str | None = None,
    search: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get members (users and teams) for a source with full details.

    Args:
        session: Database session
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        member_kind: Optional member kind filter ('user' or 'team')
        search: Optional search query for name or email
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with 'grant', 'asset', and 'member' (User or Team) keys
    """
    query = (
        select(PrimaryAssetRoleGrant, PrimaryAsset)
        .join(PrimaryAsset, PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
        )
    )

    # Filter by member kind
    if member_kind == "user":
        query = query.where(PrimaryAssetRoleGrant.principal_kind == PrincipalKind.user)
    elif member_kind == "team":
        query = query.where(PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team)
    else:
        # Include both users and teams (exclude org and public)
        query = query.where(
            or_(
                PrimaryAssetRoleGrant.principal_kind == PrincipalKind.user,
                PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
            )
        )

    # Filter by roles
    if roles:
        backend_roles = [
            PrimaryAssetRole.admin if r == "admin" else PrimaryAssetRole.viewer
            for r in roles
        ]
        query = query.where(PrimaryAssetRoleGrant.role.in_(backend_roles))

    results = session.exec(query).all()

    # Fetch users and teams separately for search and joining
    output = []
    for grant, asset in results:
        member_data = None

        if grant.principal_kind == PrincipalKind.user and grant.user_id:
            user = session.exec(select(User).where(User.id == grant.user_id)).first()
            if user:
                # Apply search filter
                if search and (
                    search.lower() not in (user.name or "").lower()
                    and search.lower() not in (user.email or "").lower()
                ):
                    continue
                member_data = {
                    "kind": "user",
                    "member": user,
                }

        elif grant.principal_kind == PrincipalKind.team and grant.team_id:
            team = session.exec(select(Team).where(Team.id == grant.team_id)).first()
            if team:
                # Apply search filter
                if search and search.lower() not in team.name.lower():
                    continue
                member_data = {
                    "kind": "team",
                    "member": team,
                }

        if member_data:
            output.append({"grant": grant, "asset": asset, **member_data})

    # Apply pagination after filtering
    return output[offset : offset + limit]


def count_source_members(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    roles: list[str] | None = None,
    member_kind: str | None = None,
    search: str | None = None,
) -> int:
    """
    Count members for a source with optional filtering.

    Args:
        session: Database session
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        member_kind: Optional member kind filter
        search: Optional search query

    Returns:
        Count of matching members
    """
    # Use the same logic as get_source_members_with_details but just count
    results = get_source_members_with_details(
        session=session,
        primary_asset_id=primary_asset_id,
        organization_id=organization_id,
        roles=roles,
        member_kind=member_kind,
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
