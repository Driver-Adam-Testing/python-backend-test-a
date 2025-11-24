"""Query-level authorization filters for SQLAlchemy queries.

These filters allow list endpoints to filter results based on user grants
without loading all records into memory first.
"""

import uuid
from typing import Any

from database.models import (
    DerivedContent,
    DocumentSource,
    Node,
    OrgMembership,
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Version,
)
from database.models_enums import PrimaryAssetKind, PrimaryAssetRole, PrincipalKind
from sqlalchemy import String, and_, case, cast, literal, true
from sqlalchemy.orm import aliased
from sqlmodel import Session, select

from shared.authorization.helpers import (
    build_grant_condition,
    get_user_team_ids,
    is_org_member,
    is_super_admin,
)
from shared.authorization.types import AssignmentType


def _grant_exists_subquery(
    user_id: uuid.UUID,
    team_ids: list[uuid.UUID],
    is_member: bool,
    organization_id: str,
    asset_id_column: Any,
    role: PrimaryAssetRole,
) -> Any:
    """Helper to build an EXISTS subquery for a specific role."""
    grant_condition = build_grant_condition(user_id, team_ids, is_member)
    return (
        select(PrimaryAssetRoleGrant)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == asset_id_column,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.role == role,
            grant_condition,
        )
        .exists()
    )


def asset_visibility_expr(
    organization_id: str, asset_id_column: Any
) -> tuple[Any, Any, Any]:
    """
    Returns SQL expression for asset visibility based on grant type, plus subqueries for joining.

    Visibility precedence: public > internal > private
    - public: Has grant with principal_kind = 'public'
    - internal: Has grant with principal_kind = 'org'
    - private: No org or public grants

    Returns:
        Tuple of (visibility_expr, org_grant_subquery, public_grant_subquery)
        The subqueries must be joined to the main query for the expression to work.
    """
    org_grant_subquery = (
        select(
            PrimaryAssetRoleGrant.primary_asset_id,
            literal(True).label("has_org_grant"),
        )
        .where(
            and_(
                PrimaryAssetRoleGrant.organization_id == organization_id,
                PrimaryAssetRoleGrant.principal_kind == PrincipalKind.org,
            )
        )
        .subquery()
    )

    public_grant_subquery = (
        select(
            PrimaryAssetRoleGrant.primary_asset_id,
            literal(True).label("has_public_grant"),
        )
        .where(
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.public,
        )
        .subquery()
    )

    visibility_case_expr = case(
        (public_grant_subquery.c.has_public_grant.is_not(None), literal("public")),
        (org_grant_subquery.c.has_org_grant.is_not(None), literal("internal")),
        else_=literal("private"),
    )

    return visibility_case_expr, org_grant_subquery, public_grant_subquery


def effective_asset_role_expr(
    db: Session, user_id: str, organization_id: str, asset_id_column: Any
) -> Any:
    """
    Returns a SQL expression that computes the effective role for a user on an asset.

    The effective role is the highest priority role among all applicable grants:
    - asset_admin (highest priority) - includes org super_admins
    - asset_member

    Note: For batch processing multiple assets, use
    acl_repository.get_user_effective_roles_for_assets_batch() instead,
    which uses the same logic but is optimized for multiple assets.

    Args:
        db: Database session
        user_id: UUID of the user
        organization_id: Organization ID
        asset_id_column: The column to match against (e.g., PrimaryAsset.id)

    Returns:
        SQL expression that evaluates to the role string, or None if no grants
    """
    # Super admins have asset_admin role on all assets
    if is_super_admin(db, user_id, organization_id):
        return literal(PrimaryAssetRole.asset_admin.value)

    team_ids = get_user_team_ids(db, user_id, organization_id)
    is_member = is_org_member(db, user_id, organization_id)

    # Check for each role in priority order
    admin_exists = _grant_exists_subquery(
        user_id,
        team_ids,
        is_member,
        organization_id,
        asset_id_column,
        PrimaryAssetRole.asset_admin,
    )
    member_exists = _grant_exists_subquery(
        user_id,
        team_ids,
        is_member,
        organization_id,
        asset_id_column,
        PrimaryAssetRole.asset_member,
    )

    return case(
        (admin_exists, PrimaryAssetRole.asset_admin.value),
        (member_exists, PrimaryAssetRole.asset_member.value),
        else_=None,
    )


def primary_asset_grant_filter(
    db: Session,
    user_id: str,
    organization_id: str,
    role: PrimaryAssetRole | None = None,
) -> Any:
    """
    Filter for PrimaryAssets where user has a grant.

    Returns a SQLAlchemy filter condition that can be added to queries
    selecting PrimaryAsset rows.

    Users can access assets if:
    1. They are a super_admin in the organization (bypass all checks)
    2. They have a grant to the PrimaryAsset via:
       - Public grants (principal_kind = 'public')
       - Direct user grants (principal_kind = 'user' AND user_id = <user_id>)
       - Team grants (principal_kind = 'team' AND team_id IN <user's teams>)
       - Org-wide grants (principal_kind = 'org')

    Example usage:
        # Basic filtering
        query = select(PrimaryAsset).where(
            PrimaryAsset.organization_id == org_id,
            primary_asset_grant_filter(db, user_id, org_id)
        )

        # Filter for admin access only
        query = select(PrimaryAsset).where(
            PrimaryAsset.organization_id == org_id,
            primary_asset_grant_filter(db, user_id, org_id, role=PrimaryAssetRole.asset_admin)
        )

        # With effective role
        role_expr = effective_asset_role_expr(db, user_id, org_id, PrimaryAsset.id)
        query = select(PrimaryAsset, role_expr.label("effective_role")).where(
            PrimaryAsset.organization_id == org_id,
            primary_asset_grant_filter(db, user_id, org_id)
        )

    Args:
        db: Database session
        user_id: UUID of the user
        organization_id: Organization ID
        role: Optional role filter (e.g., PrimaryAssetRole.asset_admin)

    Returns:
        SQLAlchemy filter condition, or True if user is super admin
    """
    if is_super_admin(db, user_id, organization_id):
        return True

    team_ids = get_user_team_ids(db, user_id, organization_id)
    is_member = is_org_member(db, user_id, organization_id)

    grant_condition = build_grant_condition(user_id, team_ids, is_member)

    conditions = [
        PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id,
        PrimaryAssetRoleGrant.organization_id == organization_id,
        grant_condition,
    ]

    if role is not None:
        conditions.append(PrimaryAssetRoleGrant.role == role)

    return select(PrimaryAssetRoleGrant).where(*conditions).exists()


def content_grant_filter(db: Session, user_id: str, organization_id: str) -> Any:
    """
    Filter for DerivedContent where user has a grant to the associated PrimaryAsset.

    Returns a SQLAlchemy filter condition that can be added to queries
    selecting DerivedContent rows.

    This traverses the relationship chain:
    DerivedContent → Node → Version → PrimaryAsset → PrimaryAssetRoleGrant

    Users can access content if:
    1. They are a super_admin in the organization (bypass all checks)
    2. They have a grant to the associated PrimaryAsset via:
       - Public grants (principal_kind = 'public')
       - Direct user grants (principal_kind = 'user' AND user_id = <user_id>)
       - Team grants (principal_kind = 'team' AND team_id IN <user's teams>)
       - Org-wide grants (principal_kind = 'org')

    Example usage:
        query = select(DerivedContent).where(
            content_grant_filter(db, user_id, org_id)
        )

    Args:
        db: Database session
        user_id: UUID of the user
        organization_id: Organization ID

    Returns:
        SQLAlchemy filter condition, or True if user is super admin
    """
    if is_super_admin(db, user_id, organization_id):
        return True  # SQLAlchemy treats True as "no filter"

    team_ids = get_user_team_ids(db, user_id, organization_id)
    is_member = is_org_member(db, user_id, organization_id)

    grant_condition = build_grant_condition(user_id, team_ids, is_member)

    # Filter: Content's PrimaryAsset must have a grant matching our conditions
    return DerivedContent.node.has(
        Node.version.has(
            Version.primary_asset.has(
                select(PrimaryAssetRoleGrant)
                .where(
                    PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id,
                    PrimaryAssetRoleGrant.organization_id == organization_id,
                    grant_condition,
                )
                .exists()
            )
        )
    )


def exclude_page_assets_filter() -> Any:
    return PrimaryAsset.kind.notin_(
        [PrimaryAssetKind.PAGE, PrimaryAssetKind.PAGE_TEMPLATE]
    )


def only_page_assets_filter() -> Any:
    return PrimaryAsset.kind.in_(
        [PrimaryAssetKind.PAGE, PrimaryAssetKind.PAGE_TEMPLATE]
    )


def page_source_authorization_filter(
    db: Session, user_id: str, organization_id: str
) -> Any:
    """
    Authorization filter for PAGE assets based on source grants.

    Pages have different authorization than regular assets:
    - Regular assets: User needs grant to the asset itself
    - Page assets: User needs grants to ALL sources referenced by the page

    A page is accessible if NO unauthorized sources exist for it.
    """
    if is_super_admin(db, user_id, organization_id):
        return true()

    team_ids = get_user_team_ids(db, user_id, organization_id)
    is_member = is_org_member(db, user_id, organization_id)
    grant_condition = build_grant_condition(user_id, team_ids, is_member)

    SourceNode = aliased(Node)
    SourceVersion = aliased(Version)

    unauthorized_source_exists = (
        select(DocumentSource)
        .join(Node, DocumentSource.page_node_id == Node.id)
        .join(Version, Node.version_id == Version.id)
        .where(Version.primary_asset_id == PrimaryAsset.id)
        .join(SourceNode, DocumentSource.source_node_id == SourceNode.id)
        .join(SourceVersion, SourceNode.version_id == SourceVersion.id)
        .where(
            ~select(PrimaryAssetRoleGrant)
            .where(
                PrimaryAssetRoleGrant.primary_asset_id
                == SourceVersion.primary_asset_id,
                PrimaryAssetRoleGrant.organization_id == organization_id,
                grant_condition,
            )
            .exists()
        )
        .exists()
    )

    return ~unauthorized_source_exists


def page_asset_grant_filter(db: Session, user_id: str, organization_id: str) -> Any:
    if is_super_admin(db, user_id, organization_id):
        return only_page_assets_filter()

    return and_(
        only_page_assets_filter(),
        page_source_authorization_filter(db, user_id, organization_id),
    )


def page_content_grant_filter(db: Session, user_id: str, organization_id: str) -> Any:
    if is_super_admin(db, user_id, organization_id):
        return DerivedContent.node.has(
            Node.version.has(Version.primary_asset.has(only_page_assets_filter()))
        )

    return DerivedContent.node.has(
        Node.version.has(
            Version.primary_asset.has(
                and_(
                    only_page_assets_filter(),
                    page_source_authorization_filter(db, user_id, organization_id),
                )
            )
        )
    )


def asset_org_grant_role_expr(organization_id: str, asset_id_column: Any) -> Any:
    """
    Returns a SQL expression for the org-level grant role on an asset.
    Returns the role if there's an org-wide grant (principal_kind = 'org'), else None.
    """
    return (
        select(PrimaryAssetRoleGrant.role)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == asset_id_column,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.org,
        )
        .scalar_subquery()
    )


def user_direct_grant_role_expr(
    user_id: str, organization_id: str, asset_id_column: Any
) -> Any:
    """
    Returns a SQL expression for the direct user grant role on an asset.
    Returns the role if there's a direct user grant (principal_kind = 'user'), else None.
    """
    return (
        select(PrimaryAssetRoleGrant.role)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == asset_id_column,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            PrimaryAssetRoleGrant.principal_kind == PrincipalKind.user,
            PrimaryAssetRoleGrant.user_id == user_id,
        )
        .scalar_subquery()
    )


def user_org_role_expr(user_id: str, organization_id: str) -> Any:
    return (
        select(OrgMembership.role)
        .where(
            OrgMembership.user_id == user_id,
            OrgMembership.org_id == organization_id,
        )
        .scalar_subquery()
    )


def assignment_type_expr(
    db: Session,
    user_id: str,
    organization_id: str,
    effective_role_expr: Any,
    source_role_expr: Any,
) -> Any:
    """
    Returns a SQL expression that computes the assignment type.

    Assignment type is 'direct' if the effective role comes from a direct user grant,
    'inherited' if it comes from super admin, org grant, or team grant.
    """
    is_super = is_super_admin(db, user_id, organization_id)

    if is_super:
        return literal(AssignmentType.INHERITED.value)

    # If source_role == effective_role AND source_role is not NULL, then 'direct', else 'inherited'
    # We need to check for non-NULL source_role because NULL means no direct grant
    # Cast enum values to text for comparison
    return case(
        (
            (source_role_expr.isnot(None))
            & (cast(source_role_expr, String) == cast(effective_role_expr, String)),
            literal(AssignmentType.DIRECT.value),
        ),
        else_=literal(AssignmentType.INHERITED.value),
    )
