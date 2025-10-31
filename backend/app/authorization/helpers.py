import uuid

from database.models import (
    OrgMembership,
    PrimaryAssetRoleGrant,
    Team,
    TeamMembership,
)
from database.models_enums import OrgRole, PrincipalKind
from sqlalchemy import ColumnElement
from sqlmodel import Session, select


def is_super_admin(db: Session, user_id: uuid.UUID, organization_id: str) -> bool:
    """Check if user is a super admin of the organization.

    Super admins bypass all authorization checks and have full access
    to all resources within their organization.
    """
    query = select(OrgMembership).where(
        OrgMembership.org_id == organization_id,
        OrgMembership.user_id == user_id,
        OrgMembership.role == OrgRole.org_super_admin,
    )
    return db.exec(query).first() is not None


def is_org_member(db: Session, user_id: uuid.UUID, organization_id: str) -> bool:
    query = select(OrgMembership).where(
        OrgMembership.org_id == organization_id,
        OrgMembership.user_id == user_id,
    )
    return db.exec(query).first() is not None


def get_user_team_ids(
    db: Session, user_id: uuid.UUID, organization_id: str
) -> list[uuid.UUID]:
    query = (
        select(TeamMembership.team_id)
        .join(Team, Team.id == TeamMembership.team_id)
        .where(
            Team.organization_id == organization_id, TeamMembership.user_id == user_id
        )
    )
    return list(db.exec(query).all())


def build_grant_condition(
    user_id: uuid.UUID, team_ids: list[uuid.UUID], is_member: bool
) -> ColumnElement[bool]:
    """Build SQLAlchemy condition for matching grants.

    Creates an OR condition that matches any applicable grant for a user:
    - Public grants (available to everyone)
    - User grants (specific to this user) - only if user is org member
    - Team grants (via team membership) - only if user is org member
    - Org-wide grants (all org members) - only if user is org member

    Args:
        user_id: UUID of the user
        team_ids: List of team UUIDs the user is a member of
        is_member: Whether user is an org member

    Returns:
        SQLAlchemy condition for grant matching
    """
    # Always check public grants
    conditions = [PrimaryAssetRoleGrant.principal_kind == PrincipalKind.public]

    if is_member:
        conditions.extend(
            [
                # Direct user grants
                (PrimaryAssetRoleGrant.principal_kind == PrincipalKind.user)
                & (PrimaryAssetRoleGrant.user_id == str(user_id)),
                # Org-wide grants
                PrimaryAssetRoleGrant.principal_kind == PrincipalKind.org,
            ]
        )

        if team_ids:
            conditions.append(
                (PrimaryAssetRoleGrant.principal_kind == PrincipalKind.team)
                & (PrimaryAssetRoleGrant.team_id.in_(team_ids))
            )

    # Combine all conditions with OR
    combined_condition = conditions[0]
    for condition in conditions[1:]:
        combined_condition = combined_condition | condition

    return combined_condition
