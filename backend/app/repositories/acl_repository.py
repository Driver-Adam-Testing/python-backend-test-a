"""Repository functions for ACL (PrimaryAssetRoleGrant) data access."""

from uuid import UUID

from app.authorization.query_filters import asset_visibility_expr
from app.schemas.user_schema import AssignmentType
from database.models import (
    OrgMembership,
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Team,
    TeamMembership,
    User,
)
from database.models_enums import (
    OrgRole,
    PrimaryAssetRole,
    PrincipalKind,
    SourceVisibility,
)
from sqlalchemy import case, literal, literal_column, union_all
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
        List of dictionaries with 'grant', 'asset', and 'visibility' keys
    """
    visibility_expr, org_grant_sub, public_grant_sub = asset_visibility_expr(
        organization_id, PrimaryAsset.id
    )

    query = (
        select(PrimaryAssetRoleGrant, PrimaryAsset, visibility_expr.label("visibility"))
        .join(PrimaryAsset, PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id)
        .outerjoin(org_grant_sub, PrimaryAsset.id == org_grant_sub.c.primary_asset_id)
        .outerjoin(
            public_grant_sub, PrimaryAsset.id == public_grant_sub.c.primary_asset_id
        )
        .options(selectinload(PrimaryAsset.most_recent_version))
        .where(
            PrimaryAssetRoleGrant.team_id == team_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
        )
    )

    if roles:
        query = query.where(PrimaryAssetRoleGrant.role.in_(roles))

    if search:
        query = query.where(PrimaryAsset.display_name.ilike(f"%{search}%"))

    query = query.order_by(PrimaryAsset.display_name).offset(offset).limit(limit)

    results = session.exec(query).all()

    return [
        {"grant": grant, "asset": asset, "visibility": visibility}
        for grant, asset, visibility in results
    ]


def get_user_effective_roles_for_assets_batch(
    session: Session,
    user_id: str,
    organization_id: str,
    asset_ids: list[UUID],
) -> dict[UUID, PrimaryAssetRole | None]:
    """
    Calculate effective roles for a user on multiple assets using the same logic
    as effective_asset_role_expr but optimized for batch processing.
    """
    from app.authorization.helpers import (
        build_grant_condition,
        get_user_team_ids,
        is_org_member,
        is_super_admin,
    )

    if not asset_ids:
        return {}

    # Super admins have asset_admin on everything
    if is_super_admin(session, user_id, organization_id):
        return {asset_id: PrimaryAssetRole.asset_admin for asset_id in asset_ids}

    team_ids = get_user_team_ids(session, user_id, organization_id)
    is_member = is_org_member(session, user_id, organization_id)
    grant_condition = build_grant_condition(user_id, team_ids, is_member)

    # Use func.max to get highest role per asset (asset_admin > asset_member)
    # This is equivalent to effective_asset_role_expr but batched
    query = (
        select(
            PrimaryAssetRoleGrant.primary_asset_id,
            func.max(PrimaryAssetRoleGrant.role).label("max_role"),
        )
        .where(
            PrimaryAssetRoleGrant.primary_asset_id.in_(asset_ids),
            PrimaryAssetRoleGrant.organization_id == organization_id,
            grant_condition,
        )
        .group_by(PrimaryAssetRoleGrant.primary_asset_id)
    )

    results = session.exec(query).all()
    asset_roles = {asset_id: role for asset_id, role in results}  # noqa: C416

    # Note: returns None for assets with no access
    return {asset_id: asset_roles.get(asset_id) for asset_id in asset_ids}


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


def _build_source_users_base_ctes(
    primary_asset_id: UUID,
    organization_id: str,
    assignment_type: AssignmentType | None = None,
) -> tuple:
    """
    Build the base CTEs and effective_roles subquery for source users queries.

    This helper function constructs the common query components used by both
    get_source_users_with_details and count_source_users.

    Args:
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        assignment_type: Optional assignment type filter ('direct' or 'inherited')

    Returns:
        Tuple of (direct_grants_cte, team_grants_cte, org_grants_cte, effective_roles_subquery)
    """
    # CTE 1: Direct user grants
    direct_grants_cte = (
        select(
            PrimaryAssetRoleGrant.user_id,
            PrimaryAssetRoleGrant.role.label("grant_role"),
            literal("direct").label("assignment_type"),
            PrimaryAssetRoleGrant.created_at,
        )
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.user,
            PrimaryAssetRoleGrant.user_id.is_not(None),
        )
        .cte("direct_grants")
    )

    # CTE 2: Team-based grants (inherited)
    team_grants_cte = (
        select(
            TeamMembership.user_id,
            PrimaryAssetRoleGrant.role.label("grant_role"),
            literal("inherited").label("assignment_type"),
            PrimaryAssetRoleGrant.created_at,
        )
        .select_from(PrimaryAssetRoleGrant)
        .join(TeamMembership, TeamMembership.team_id == PrimaryAssetRoleGrant.team_id)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
            PrimaryAssetRoleGrant.team_id.is_not(None),
        )
        .cte("team_grants")
    )

    # CTE 3: Org-wide grants (inherited through org membership)
    org_grants_cte = (
        select(
            OrgMembership.user_id,
            PrimaryAssetRoleGrant.role.label("grant_role"),
            literal("inherited").label("assignment_type"),
            PrimaryAssetRoleGrant.created_at,
        )
        .select_from(PrimaryAssetRoleGrant)
        .join(
            OrgMembership,
            OrgMembership.org_id == PrimaryAssetRoleGrant.organization_id,
        )
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.org,
        )
        .cte("org_grants")
    )

    # CTE 4: Public grants (inherited through org membership)
    public_grants_cte = (
        select(
            OrgMembership.user_id,
            PrimaryAssetRoleGrant.role.label("grant_role"),
            literal("inherited").label("assignment_type"),
            PrimaryAssetRoleGrant.created_at,
        )
        .select_from(PrimaryAssetRoleGrant)
        .join(
            OrgMembership,
            OrgMembership.org_id == PrimaryAssetRoleGrant.organization_id,
        )
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.public,
        )
        .cte("public_grants")
    )

    # CTE 5: Super admin grants (super admins have implicit asset_admin access)
    super_admin_grants_cte = (
        select(
            OrgMembership.user_id,
            literal_column("'asset_admin'::primaryassetrole").label("grant_role"),
            literal("inherited").label("assignment_type"),
            literal_column("NULL::timestamp").label("created_at"),
        )
        .select_from(OrgMembership)
        .where(
            OrgMembership.org_id == organization_id,
            OrgMembership.role == OrgRole.org_super_admin,
        )
        .cte("super_admin_grants")
    )

    # Build union based on assignment_type filter
    if assignment_type == "direct":
        all_grants = select(
            direct_grants_cte.c.user_id,
            direct_grants_cte.c.grant_role,
            direct_grants_cte.c.assignment_type,
            direct_grants_cte.c.created_at,
        ).subquery("all_grants")
    elif assignment_type == "inherited":
        all_grants = union_all(
            select(
                team_grants_cte.c.user_id,
                team_grants_cte.c.grant_role,
                team_grants_cte.c.assignment_type,
                team_grants_cte.c.created_at,
            ),
            select(
                org_grants_cte.c.user_id,
                org_grants_cte.c.grant_role,
                org_grants_cte.c.assignment_type,
                org_grants_cte.c.created_at,
            ),
            select(
                public_grants_cte.c.user_id,
                public_grants_cte.c.grant_role,
                public_grants_cte.c.assignment_type,
                public_grants_cte.c.created_at,
            ),
            select(
                super_admin_grants_cte.c.user_id,
                super_admin_grants_cte.c.grant_role,
                super_admin_grants_cte.c.assignment_type,
                super_admin_grants_cte.c.created_at,
            ),
        ).subquery("all_grants")
    else:
        all_grants = union_all(
            select(
                direct_grants_cte.c.user_id,
                direct_grants_cte.c.grant_role,
                direct_grants_cte.c.assignment_type,
                direct_grants_cte.c.created_at,
            ),
            select(
                team_grants_cte.c.user_id,
                team_grants_cte.c.grant_role,
                team_grants_cte.c.assignment_type,
                team_grants_cte.c.created_at,
            ),
            select(
                org_grants_cte.c.user_id,
                org_grants_cte.c.grant_role,
                org_grants_cte.c.assignment_type,
                org_grants_cte.c.created_at,
            ),
            select(
                public_grants_cte.c.user_id,
                public_grants_cte.c.grant_role,
                public_grants_cte.c.assignment_type,
                public_grants_cte.c.created_at,
            ),
            select(
                super_admin_grants_cte.c.user_id,
                super_admin_grants_cte.c.grant_role,
                super_admin_grants_cte.c.assignment_type,
                super_admin_grants_cte.c.created_at,
            ),
        ).subquery("all_grants")

    # Use ROW_NUMBER to find the winning grant per user while maintaining
    # the relationship between role and assignment_type.
    # Priority order:
    # 1. Highest role (asset_admin > asset_member)
    # 2. Prefer direct over inherited for same role
    # 3. Earliest created_at as tiebreaker
    role_priority = case(
        (all_grants.c.grant_role == PrimaryAssetRole.asset_admin, 2),
        (all_grants.c.grant_role == PrimaryAssetRole.asset_member, 1),
        else_=0,
    )

    assignment_priority = case(
        (all_grants.c.assignment_type == "direct", 2),
        (all_grants.c.assignment_type == "inherited", 1),
        else_=0,
    )

    # Rank grants per user, maintaining the relationship between role and assignment_type
    ranked_grants = (
        select(
            all_grants.c.user_id,
            all_grants.c.grant_role,
            all_grants.c.assignment_type,
            all_grants.c.created_at,
            func.row_number()
            .over(
                partition_by=all_grants.c.user_id,
                order_by=[
                    role_priority.desc(),
                    assignment_priority.desc(),
                    all_grants.c.created_at,
                ],
            )
            .label("rn"),
        )
        .select_from(all_grants)
        .subquery("ranked_grants")
    )

    # Take only the top-ranked grant per user (rn=1)
    effective_roles = (
        select(
            ranked_grants.c.user_id,
            ranked_grants.c.grant_role.label("effective_role"),
            ranked_grants.c.assignment_type,
            ranked_grants.c.created_at,
        )
        .where(ranked_grants.c.rn == 1)
        .subquery("effective_roles")
    )

    return direct_grants_cte, team_grants_cte, org_grants_cte, effective_roles


def get_source_users_with_details(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    search: str | None = None,
    assignment_type: AssignmentType | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get users for a source with full details using efficient SQL.

    Returns all users with access including:
    - Users with direct grants to the source
    - Users who are members of teams that have grants to the source
    - Users who are org members when the source has org-wide grants

    Args:
        session: Database session
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        search: Optional search query for name or email
        assignment_type: Optional assignment type filter ('direct' or 'inherited')
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with user data: user_id, name, email, effective_role,
        assignment_type, org_role, is_super_admin, created_at
    """
    # Build base CTEs using helper function
    direct_grants_cte, team_grants_cte, org_grants_cte, effective_roles = (
        _build_source_users_base_ctes(
            primary_asset_id, organization_id, assignment_type
        )
    )

    # CTE 4: Highest team grant role per user (for team_source_role field)
    team_source_roles = (
        select(
            TeamMembership.user_id,
            func.max(PrimaryAssetRoleGrant.role).label("team_source_role"),
        )
        .select_from(PrimaryAssetRoleGrant)
        .join(TeamMembership, TeamMembership.team_id == PrimaryAssetRoleGrant.team_id)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
            PrimaryAssetRoleGrant.team_id.is_not(None),
        )
        .group_by(TeamMembership.user_id)
        .cte("team_source_roles")
    )

    # Scalar subquery: Org-wide asset grant (for asset_org_role field)
    asset_org_role_subquery = (
        select(PrimaryAssetRoleGrant.role)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.org,
        )
        .limit(1)
        .scalar_subquery()
    )

    # Main query: Join with User, OrgMembership, and granular role CTEs
    query = (
        select(
            User.id.label("user_id"),
            User.name,
            User.email,
            effective_roles.c.effective_role,
            effective_roles.c.assignment_type,
            effective_roles.c.created_at,
            OrgMembership.role.label("org_role"),
            # Granular role fields
            direct_grants_cte.c.grant_role.label("user_grant_role"),
            team_source_roles.c.team_source_role,
            asset_org_role_subquery.label("asset_org_role"),
        )
        .select_from(effective_roles)
        .join(User, User.id == effective_roles.c.user_id)
        .outerjoin(
            OrgMembership,
            (OrgMembership.user_id == User.id)
            & (OrgMembership.org_id == organization_id),
        )
        .outerjoin(direct_grants_cte, direct_grants_cte.c.user_id == User.id)
        .outerjoin(team_source_roles, team_source_roles.c.user_id == User.id)
    )

    # Apply filters
    if roles:
        query = query.where(effective_roles.c.effective_role.in_(roles))

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.name.ilike(search_pattern)) | (User.email.ilike(search_pattern))
        )

    # Order and paginate
    query = query.order_by(User.name).offset(offset).limit(limit)

    results = session.exec(query).all()

    # Convert to dictionary format
    return [
        {
            "user_id": row.user_id,
            "name": row.name or "",
            "email": row.email or "",
            "effective_role": row.effective_role,
            "assignment_type": row.assignment_type,
            "created_at": row.created_at.isoformat() if row.created_at else "",
            "org_role": row.org_role or OrgRole.org_member,
            "is_super_admin": row.org_role == OrgRole.org_super_admin
            if row.org_role
            else False,
            # Granular role fields
            "user_org_role": row.org_role.value if row.org_role else None,
            "asset_org_role": row.asset_org_role.value if row.asset_org_role else None,
            "team_source_role": row.team_source_role.value
            if row.team_source_role
            else None,
            "user_grant_role": row.user_grant_role.value
            if row.user_grant_role
            else None,
        }
        for row in results
    ]


def get_source_teams_with_details(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    user_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    search: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    """
    Get teams for a source with full details using efficient SQL.

    Args:
        session: Database session
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        user_id: Current user's ID (to fetch their team membership role)
        roles: Optional list of roles to filter by
        search: Optional search query for team name
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dictionaries with 'grant', 'asset', 'kind', 'member' (Team), and 'user_team_role' keys
    """
    query = (
        select(PrimaryAssetRoleGrant, Team, TeamMembership.role)
        .join(Team, PrimaryAssetRoleGrant.team_id == Team.id)
        .outerjoin(
            TeamMembership,
            (TeamMembership.team_id == Team.id) & (TeamMembership.user_id == user_id),
        )
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
        )
    )

    if roles:
        query = query.where(PrimaryAssetRoleGrant.role.in_(roles))

    if search:
        query = query.where(Team.name.ilike(f"%{search}%"))

    query = query.order_by(Team.name).offset(offset).limit(limit)
    results = session.exec(query).all()

    # Return in format compatible with existing service layer
    asset = session.exec(
        select(PrimaryAsset).where(PrimaryAsset.id == primary_asset_id)
    ).first()
    return [
        {
            "grant": grant,
            "asset": asset,
            "kind": "team",
            "member": team,
            "user_team_role": user_team_role,
        }
        for grant, team, user_team_role in results
    ]


def count_source_users(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    search: str | None = None,
    assignment_type: AssignmentType | None = None,
) -> int:
    """
    Count users for a source with optional filtering using efficient SQL.

    Args:
        session: Database session
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        search: Optional search query
        assignment_type: Optional assignment type filter ('direct' or 'inherited')

    Returns:
        Count of matching users
    """
    # Build base CTEs using helper function
    _, _, _, effective_roles = _build_source_users_base_ctes(
        primary_asset_id, organization_id, assignment_type
    )

    # Count query with filters
    count_query = select(func.count()).select_from(effective_roles)

    # Join User for search filter
    if search or roles:
        count_query = count_query.join(User, User.id == effective_roles.c.user_id)

    if roles:
        count_query = count_query.where(effective_roles.c.effective_role.in_(roles))

    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            (User.name.ilike(search_pattern)) | (User.email.ilike(search_pattern))
        )

    return session.exec(count_query).one()


def count_source_teams(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    roles: list[PrimaryAssetRole] | None = None,
    search: str | None = None,
) -> int:
    """
    Count teams for a source with optional filtering using efficient SQL.

    Args:
        session: Database session
        primary_asset_id: Primary asset (source) ID
        organization_id: Organization ID
        roles: Optional list of roles to filter by
        search: Optional search query

    Returns:
        Count of matching teams
    """
    query = (
        select(func.count())
        .select_from(PrimaryAssetRoleGrant)
        .join(Team, PrimaryAssetRoleGrant.team_id == Team.id)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
        )
    )

    if roles:
        query = query.where(PrimaryAssetRoleGrant.role.in_(roles))

    if search:
        query = query.where(Team.name.ilike(f"%{search}%"))

    return session.exec(query).one()


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


def get_source_team_memberships_batch(
    session: Session,
    source_id: UUID,
    user_ids: list[str],
    organization_id: str,
) -> dict[str, list[dict]]:
    """
    Batch fetch team memberships for multiple users that grant access to a source.

    Returns only teams that have grants to the specified source.

    Args:
        session: Database session
        source_id: Source (primary asset) ID
        user_ids: List of user IDs to fetch team memberships for
        organization_id: Organization ID

    Returns:
        Dictionary mapping user_id to list of TeamMembershipInfo dictionaries with keys:
        - team_id: UUID
        - display_name: str
        - team_role: str
        - source_role: PrimaryAssetRole
    """
    if not user_ids:
        return {}

    # Get all team grants for this source
    team_grants_query = select(PrimaryAssetRoleGrant).where(
        PrimaryAssetRoleGrant.primary_asset_id == source_id,
        PrimaryAssetRoleGrant.organization_id == organization_id,
        PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team,
        PrimaryAssetRoleGrant.team_id.is_not(None),
    )
    team_grants = session.exec(team_grants_query).all()

    # Create mapping of team_id -> source_role
    team_source_roles = {
        grant.team_id: grant.role for grant in team_grants if grant.team_id
    }

    if not team_source_roles:
        return {user_id: [] for user_id in user_ids}

    # Batch fetch team memberships for all users, filtered to teams with source access
    query = (
        select(TeamMembership, Team)
        .join(Team, TeamMembership.team_id == Team.id)
        .where(
            TeamMembership.user_id.in_(user_ids),
            Team.organization_id == organization_id,
            Team.id.in_(list(team_source_roles.keys())),
        )
        .order_by(TeamMembership.user_id, Team.name)
    )

    results = session.exec(query).all()

    # Group by user_id
    teams_by_user: dict[str, list[dict]] = {user_id: [] for user_id in user_ids}
    for membership, team in results:
        teams_by_user[membership.user_id].append(
            {
                "team_id": team.id,
                "display_name": team.name,
                "team_role": membership.role.value,
                "source_role": team_source_roles[team.id],
            }
        )

    return teams_by_user


def create_default_visibility_grants(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    creator_user_id: str,
    visibility: SourceVisibility,
) -> list[PrimaryAssetRoleGrant]:
    grants = []

    creator_grant = PrimaryAssetRoleGrant(
        primary_asset_id=primary_asset_id,
        organization_id=organization_id,
        principal_kind=PrincipalKind.user,
        user_id=creator_user_id,
        role=PrimaryAssetRole.asset_admin,
    )
    session.add(creator_grant)
    grants.append(creator_grant)

    if visibility == SourceVisibility.internal:
        org_grant = PrimaryAssetRoleGrant(
            primary_asset_id=primary_asset_id,
            organization_id=organization_id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
        )
        session.add(org_grant)
        grants.append(org_grant)
    elif visibility == SourceVisibility.public:
        public_grant = PrimaryAssetRoleGrant(
            primary_asset_id=primary_asset_id,
            organization_id=organization_id,
            principal_kind=PrincipalKind.public,
            role=PrimaryAssetRole.asset_member,
        )
        session.add(public_grant)
        grants.append(public_grant)

    return grants


def update_asset_visibility(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
    visibility: SourceVisibility,
) -> None:
    """
    Update asset visibility by managing org and public grants.
    Preserves all user and team grants. Only modifies org/public grants.
    """
    existing_grants = session.exec(
        select(PrimaryAssetRoleGrant).where(
            PrimaryAssetRoleGrant.primary_asset_id == primary_asset_id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind.in_(
                [PrincipalKind.org, PrincipalKind.public]
            ),
        )
    ).all()

    for grant in existing_grants:
        session.delete(grant)

    if visibility == SourceVisibility.internal:
        org_grant = PrimaryAssetRoleGrant(
            primary_asset_id=primary_asset_id,
            organization_id=organization_id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
        )
        session.add(org_grant)
    elif visibility == SourceVisibility.public:
        public_grant = PrimaryAssetRoleGrant(
            primary_asset_id=primary_asset_id,
            organization_id=organization_id,
            principal_kind=PrincipalKind.public,
            role=PrimaryAssetRole.asset_member,
        )
        session.add(public_grant)

    session.commit()
