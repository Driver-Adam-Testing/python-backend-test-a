"""Repository functions for Admin Sources data access."""

from uuid import UUID

from app.authorization.helpers import is_super_admin
from app.authorization.query_filters import (
    effective_asset_role_expr,
    primary_asset_grant_filter,
)
from database.models import (
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    PrimaryAssetTag,
    Tag,
    TeamMembership,
)
from database.models_enums import PrimaryAssetKind, PrimaryAssetRole
from sqlmodel import Session, and_, func, select


def get_sources_with_counts(
    session: Session,
    user_id: str,
    organization_id: str,
    search: str | None = None,
    kinds: list[str] | None = None,
    tag_ids: list[str] | None = None,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """
    Get sources with member and team counts for admin view.

    Args:
        session: Database session
        organization_id: Organization ID
        search: Optional search query for display_name
        kinds: Optional list of asset kinds to filter
        tag_ids: Optional list of tag IDs to filter
        sort_by: Field to sort by
        sort_direction: Sort direction (ASC/DESC)
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of dicts with asset, members_count, and teams_count
    """
    # Subquery for member counts (user grants)
    members_count_subquery = (
        select(
            PrimaryAssetRoleGrant.primary_asset_id,
            func.count(PrimaryAssetRoleGrant.id).label("members_count"),
        )
        .where(
            and_(
                PrimaryAssetRoleGrant.organization_id == organization_id,
                PrimaryAssetRoleGrant.user_id.is_not(None),
            )
        )
        .group_by(PrimaryAssetRoleGrant.primary_asset_id)
        .subquery()
    )

    # Subquery for team counts
    teams_count_subquery = (
        select(
            PrimaryAssetRoleGrant.primary_asset_id,
            func.count(PrimaryAssetRoleGrant.id).label("teams_count"),
        )
        .where(
            and_(
                PrimaryAssetRoleGrant.organization_id == organization_id,
                PrimaryAssetRoleGrant.team_id.is_not(None),
            )
        )
        .group_by(PrimaryAssetRoleGrant.primary_asset_id)
        .subquery()
    )
    # TODO: adjust to filter down assets that the user has asset_admin effective role
    # Main query
    role_expr = effective_asset_role_expr(
        session, user_id, organization_id, PrimaryAsset.id
    )
    query = (
        select(
            PrimaryAsset,
            role_expr.label("effective_role"),
            func.coalesce(members_count_subquery.c.members_count, 0).label(
                "members_count"
            ),
            func.coalesce(teams_count_subquery.c.teams_count, 0).label("teams_count"),
        )
        .outerjoin(
            members_count_subquery,
            PrimaryAsset.id == members_count_subquery.c.primary_asset_id,
        )
        .outerjoin(
            teams_count_subquery,
            PrimaryAsset.id == teams_count_subquery.c.primary_asset_id,
        )
        .where(
            PrimaryAsset.organization_id == organization_id,
            primary_asset_grant_filter(session, user_id, organization_id),
            PrimaryAsset.kind.in_([PrimaryAssetKind.CODEBASE, PrimaryAssetKind.FILE]),
        )
    )

    if not is_super_admin(session, user_id, organization_id):
        user_teams_query = select(TeamMembership.team_id).where(
            TeamMembership.user_id == user_id
        )

        query = (
            query.join(
                PrimaryAssetRoleGrant,
                PrimaryAsset.id == PrimaryAssetRoleGrant.primary_asset_id,
            )
            .where(PrimaryAssetRoleGrant.role == PrimaryAssetRole.asset_admin)
            .where(
                and_(
                    PrimaryAssetRoleGrant.organization_id == organization_id,
                    # User has access through direct grant OR team grant
                    (PrimaryAssetRoleGrant.user_id == user_id)
                    | (PrimaryAssetRoleGrant.team_id.in_(user_teams_query)),
                )
            )
            .distinct()
        )

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(PrimaryAsset.display_name.ilike(search_pattern))

    # Apply kind filter
    if kinds:
        query = query.where(PrimaryAsset.kind.in_(kinds))

    # Apply tag filter
    if tag_ids:
        tag_uuids = [UUID(tag_id) for tag_id in tag_ids]
        query = (
            query.join(
                PrimaryAssetTag, PrimaryAssetTag.primary_asset_id == PrimaryAsset.id
            )
            .join(Tag, Tag.id == PrimaryAssetTag.tag_id)
            .where(Tag.id.in_(tag_uuids))
            .distinct()
        )

    # Apply sorting
    sort_column = getattr(PrimaryAsset, sort_by, PrimaryAsset.updated_at)
    if sort_direction.upper() == "ASC":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute and build results
    results = session.exec(query).all()

    return [
        {
            "asset": row[0],
            "members_count": row[1],
            "teams_count": row[2],
        }
        for row in results
    ]


def count_sources(
    session: Session,
    user_id: str,
    organization_id: str,
    search: str | None = None,
    kinds: list[str] | None = None,
    tag_ids: list[str] | None = None,
) -> int:
    """
    Count sources matching filters.

    Args:
        session: Database session
        user_id: User ID for ACL filtering
        organization_id: Organization ID
        search: Optional search query
        kinds: Optional list of asset kinds
        tag_ids: Optional list of tag IDs

    Returns:
        Count of matching sources
    """
    query = (
        select(func.count())
        .select_from(PrimaryAsset)
        .where(PrimaryAsset.organization_id == organization_id)
    )

    if not is_super_admin(session, user_id, organization_id):
        user_teams_query = select(TeamMembership.team_id).where(
            TeamMembership.user_id == user_id
        )

        query = (
            query.join(
                PrimaryAssetRoleGrant,
                PrimaryAsset.id == PrimaryAssetRoleGrant.primary_asset_id,
            )
            .where(PrimaryAssetRoleGrant.role == PrimaryAssetRole.asset_admin)
            .where(
                and_(
                    PrimaryAssetRoleGrant.organization_id == organization_id,
                    # User has access through direct grant OR team grant
                    (PrimaryAssetRoleGrant.user_id == user_id)
                    | (PrimaryAssetRoleGrant.team_id.in_(user_teams_query)),
                )
            )
            .distinct()
        )

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(PrimaryAsset.display_name.ilike(search_pattern))

    # Apply kind filter
    if kinds:
        query = query.where(PrimaryAsset.kind.in_(kinds))

    # Apply tag filter
    if tag_ids:
        tag_uuids = [UUID(tag_id) for tag_id in tag_ids]
        query = (
            query.join(
                PrimaryAssetTag, PrimaryAssetTag.primary_asset_id == PrimaryAsset.id
            )
            .join(Tag, Tag.id == PrimaryAssetTag.tag_id)
            .where(Tag.id.in_(tag_uuids))
            .distinct()
        )

    return session.exec(query).one()
