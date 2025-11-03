"""Query-level authorization filters for SQLAlchemy queries.

These filters allow list endpoints to filter results based on user grants
without loading all records into memory first.
"""

import uuid
from typing import Any

from database.models import (
    DerivedContent,
    Node,
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Version,
)
from sqlmodel import Session, select

from .helpers import (
    build_grant_condition,
    get_user_team_ids,
    is_org_member,
    is_super_admin,
)


def primary_asset_grant_filter(db: Session, user_id: str, organization_id: str) -> Any:
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
        query = select(PrimaryAsset).where(
            PrimaryAsset.organization_id == org_id,
            primary_asset_grant_filter(db, user_id, org_id)
        )

    Args:
        db: Database session
        user_id: UUID of the user
        organization_id: Organization ID

    Returns:
        SQLAlchemy filter condition, or True if user is super admin
    """
    if is_super_admin(db, user_id, organization_id):
        return True

    team_ids = get_user_team_ids(db, user_id, organization_id)
    is_member = is_org_member(db, user_id, organization_id)

    grant_condition = build_grant_condition(user_id, team_ids, is_member)

    return (
        select(PrimaryAssetRoleGrant)
        .where(
            PrimaryAssetRoleGrant.primary_asset_id == PrimaryAsset.id,
            PrimaryAssetRoleGrant.organization_id == organization_id,
            grant_condition,
        )
        .exists()
    )


def content_grant_filter(db: Session, user_id: uuid.UUID, organization_id: str) -> Any:
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
