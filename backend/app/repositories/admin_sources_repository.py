"""Repository functions for Admin Sources data access."""

from typing import Any
from uuid import UUID

from app.authorization.query_filters import (
    asset_visibility_expr,
    effective_asset_role_expr,
    exclude_page_assets_filter,
    primary_asset_grant_filter,
)
from database.models import (
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    PrimaryAssetTag,
    Tag,
)
from database.models_enums import PrimaryAssetRole, SourceVisibility
from sqlmodel import Session, and_, func, select


def _apply_common_filters(
    query: Any,
    search: str | None,
    kinds: list[str] | None,
    tag_ids: list[str] | None,
    visibility_expr: Any = None,
    visibility: list[SourceVisibility] | None = None,
) -> Any:
    if search:
        search_pattern = f"%{search}%"
        query = query.where(PrimaryAsset.display_name.ilike(search_pattern))

    if kinds:
        query = query.where(PrimaryAsset.kind.in_(kinds))

    if visibility and visibility_expr is not None:
        query = query.where(visibility_expr.in_(visibility))

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

    return query


def get_sources_with_counts(
    session: Session,
    user_id: str,
    organization_id: str,
    search: str | None = None,
    kinds: list[str] | None = None,
    tag_ids: list[str] | None = None,
    visibility: list[SourceVisibility] | None = None,
    sort_by: str = "updated_at",
    sort_direction: str = "DESC",
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """
    Only returns sources where user has effective admin role.
    Excludes Pages (only Codebases and PDFs).
    """
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

    visibility_expr, org_grant_subquery, public_grant_subquery = asset_visibility_expr(
        organization_id, PrimaryAsset.id
    )

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
            visibility_expr.label("visibility"),
        )
        .outerjoin(
            members_count_subquery,
            PrimaryAsset.id == members_count_subquery.c.primary_asset_id,
        )
        .outerjoin(
            teams_count_subquery,
            PrimaryAsset.id == teams_count_subquery.c.primary_asset_id,
        )
        .outerjoin(
            org_grant_subquery,
            PrimaryAsset.id == org_grant_subquery.c.primary_asset_id,
        )
        .outerjoin(
            public_grant_subquery,
            PrimaryAsset.id == public_grant_subquery.c.primary_asset_id,
        )
        .where(
            PrimaryAsset.organization_id == organization_id,
            primary_asset_grant_filter(
                session, user_id, organization_id, role=PrimaryAssetRole.asset_admin
            ),
            exclude_page_assets_filter(),
        )
    )

    query = _apply_common_filters(
        query, search, kinds, tag_ids, visibility_expr, visibility
    )

    sort_column = getattr(PrimaryAsset, sort_by, PrimaryAsset.updated_at)
    if sort_direction.upper() == "ASC":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    query = query.offset(offset).limit(limit)
    results = session.exec(query).all()

    return [
        {
            "asset": row[0],
            "members_count": row[2],
            "teams_count": row[3],
            "visibility": row[4],
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
    visibility: list[SourceVisibility] | None = None,
) -> int:
    """
    Only counts sources where user has effective admin role.
    Excludes Pages (only Codebases and PDFs).
    """
    query = select(func.count()).select_from(PrimaryAsset)

    visibility_expr = None
    if visibility:
        visibility_expr, org_grant_subquery, public_grant_subquery = (
            asset_visibility_expr(organization_id, PrimaryAsset.id)
        )
        query = query.outerjoin(
            org_grant_subquery,
            PrimaryAsset.id == org_grant_subquery.c.primary_asset_id,
        ).outerjoin(
            public_grant_subquery,
            PrimaryAsset.id == public_grant_subquery.c.primary_asset_id,
        )

    query = query.where(
        PrimaryAsset.organization_id == organization_id,
        primary_asset_grant_filter(
            session, user_id, organization_id, role=PrimaryAssetRole.asset_admin
        ),
        exclude_page_assets_filter(),
    )

    query = _apply_common_filters(
        query, search, kinds, tag_ids, visibility_expr, visibility
    )

    return session.exec(query).one()
