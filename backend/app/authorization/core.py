"""Action-based authorization with entitlement checks."""

import uuid
from dataclasses import dataclass

from database.models import (
    OrgMembership,
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    RoleActionAllowAsset,
    RoleActionAllowOrg,
    RoleActionAllowTeam,
    Team,
    TeamMembership,
)
from database.models_enums import (
    OrgRole,
    PrimaryAssetRole,
    TeamRole,
)
from sqlmodel import Session, select

from .helpers import (
    build_grant_condition,
    get_user_team_ids,
    is_org_member,
    is_super_admin,
)


@dataclass
class AuthContext:
    """Context for authorization checks."""

    db: Session
    user_id: uuid.UUID
    organization_id: str


@dataclass
class AccessDecision:
    """Result of an authorization check."""

    allowed: bool
    role: str | None
    reasons: list[str]
    capability_failures: list[str]


# def _cap_value(db: Session, organization_id: str, key: str) -> Union[bool, int, dict, None]:
#     """Get the effective capability value for an organization.
#
#     Prefers org-specific override, falls back to plan default.
#     """
#     # First check for org override
#     override_query = select(OrgCapabilityOverride).where(
#         OrgCapabilityOverride.organization_id == organization_id,
#         OrgCapabilityOverride.capability_key == key
#     )
#     override = db.exec(override_query).first()
#
#     if override:
#         if override.value_bool is not None:
#             return override.value_bool
#         if override.value_int is not None:
#             return override.value_int
#         if override.value_json is not None:
#             return override.value_json
#
#     # Fall back to plan capability
#     plan_cap_query = (
#         select(PlanCapability)
#         .join(OrganizationPlan, OrganizationPlan.plan_id == PlanCapability.plan_id)
#         .where(
#             OrganizationPlan.organization_id == organization_id,
#             OrganizationPlan.is_current == True,
#             PlanCapability.capability_key == key
#         )
#     )
#     plan_cap = db.exec(plan_cap_query).first()
#
#     if plan_cap:
#         if plan_cap.value_bool is not None:
#             return plan_cap.value_bool
#         if plan_cap.value_int is not None:
#             return plan_cap.value_int
#         if plan_cap.value_json is not None:
#             return plan_cap.value_json
#
#     return None
#
#
# def _required_caps(db: Session, action_key: str) -> List[str]:
#     """Get required capabilities for an action."""
#     query = select(ActionCapabilityRequirement.capability_key).where(
#         ActionCapabilityRequirement.action_key == action_key
#     )
#     return [row for row in db.exec(query).all()]


# def _entitlements_ok(db: Session, organization_id: str, action_key: str) -> Tuple[bool, List[str]]:
#     """Check if organization has required entitlements for an action."""
#     required = _required_caps(db, action_key)
#     failures = []
#
#     for cap_key in required:
#         value = _cap_value(db, organization_id, cap_key)
#         # For boolean capabilities, check if True
#         if isinstance(value, bool):
#             if not value:
#                 failures.append(cap_key)
#         # For int capabilities, we'd need context about what to check against
#         # For now, just ensure it's not None
#         elif value is None:
#             failures.append(cap_key)
#
#     return (len(failures) == 0, failures)


def _grant_rows(
    db: Session,
    organization_id: str,
    asset_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[PrimaryAssetRoleGrant]:
    """Get all applicable grant rows for a user on an asset."""
    team_ids = get_user_team_ids(db, user_id, organization_id)
    is_member = is_org_member(db, user_id, organization_id)

    # Build grant condition using shared helper
    grant_condition = build_grant_condition(user_id, team_ids, is_member)

    query = select(PrimaryAssetRoleGrant).where(
        PrimaryAssetRoleGrant.organization_id == organization_id,
        PrimaryAssetRoleGrant.primary_asset_id == asset_id,
        grant_condition,
    )

    return list(db.exec(query).all())


def _effective_asset_role(
    db: Session, organization_id: str, asset_id: uuid.UUID, user_id: uuid.UUID
) -> PrimaryAssetRole | None:
    """Get the effective role for a user on an asset."""
    rows = _grant_rows(db, organization_id, asset_id, user_id)
    roles = {r.role for r in rows}  # Keep as enum objects, not .value

    if PrimaryAssetRole.asset_admin in roles:
        return PrimaryAssetRole.asset_admin
    if PrimaryAssetRole.asset_viewer in roles:
        return PrimaryAssetRole.asset_viewer
    return None  # No access


def _role_allows_asset_action(
    db: Session, role: PrimaryAssetRole | None, action_key: str
) -> bool:
    """Check if a role allows an action on an asset kind."""
    if role is None:
        return False

    query = select(RoleActionAllowAsset).where(
        RoleActionAllowAsset.role == role,
        RoleActionAllowAsset.action_key == action_key,
    )
    return db.exec(query).first() is not None


def _org_role(db: Session, user_id: uuid.UUID, organization_id: str) -> OrgRole | None:
    """Get user's org role."""
    query = select(OrgMembership.role).where(
        OrgMembership.org_id == organization_id,
        OrgMembership.user_id == user_id,
    )
    result = db.exec(query).first()
    return result if result else None


def _role_allows_org_action(db: Session, role: OrgRole, action_key: str) -> bool:
    """Check if an org role allows an action."""
    query = select(RoleActionAllowOrg).where(
        RoleActionAllowOrg.role == role,
        RoleActionAllowOrg.action_key == action_key,
    )
    return db.exec(query).first() is not None


def _team_role(
    db: Session, team_id: uuid.UUID, user_id: uuid.UUID, organization_id: str
) -> TeamRole | None:
    """Get user's role in a team."""
    query = (
        select(TeamMembership.role)
        .join(Team, Team.id == TeamMembership.team_id)
        .where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_id,
            Team.organization_id == organization_id,
        )
    )
    result = db.exec(query).first()
    return result if result else None


def _role_allows_team_action(db: Session, role: TeamRole, action_key: str) -> bool:
    """Check if a team role allows an action."""
    query = select(RoleActionAllowTeam).where(
        RoleActionAllowTeam.role == role,
        RoleActionAllowTeam.action_key == action_key,
    )
    return db.exec(query).first() is not None


def authorize_asset_action(
    ctx: AuthContext, asset_id: uuid.UUID, action_key: str
) -> AccessDecision:
    """Authorize an action on an asset."""
    # Check entitlements first
    # ent_ok, cap_fails = _entitlements_ok(ctx.db, ctx.organization_id, action_key)
    # if not ent_ok:
    #     return AccessDecision(False, None, ["plan_denied"], cap_fails)

    # Check asset exists and belongs to org
    asset = ctx.db.get(PrimaryAsset, asset_id)
    if asset is None or asset.organization_id != ctx.organization_id:
        return AccessDecision(False, None, ["asset_not_found_or_wrong_org"], [])

    # Super admins bypass role checks
    if is_super_admin(ctx.db, ctx.user_id, ctx.organization_id):
        return AccessDecision(
            True, PrimaryAssetRole.asset_admin.value, ["org_super_admin"], []
        )

    # Check role-based access
    role = _effective_asset_role(ctx.db, ctx.organization_id, asset_id, ctx.user_id)
    if _role_allows_asset_action(ctx.db, role, action_key):
        return AccessDecision(True, role.value if role else None, ["role_allows"], [])

    return AccessDecision(False, role.value if role else None, ["role_denied"], [])


def authorize_org_action(ctx: AuthContext, action_key: str) -> AccessDecision:
    """Authorize an org-level action."""
    # Check entitlements first
    # ent_ok, cap_fails = _entitlements_ok(ctx.db, ctx.organization_id, action_key)
    # if not ent_ok:
    #     return AccessDecision(False, None, ["plan_denied"], cap_fails)

    # Super admins bypass role checks
    if is_super_admin(ctx.db, ctx.user_id, ctx.organization_id):
        return AccessDecision(
            True, OrgRole.org_super_admin.value, ["org_super_admin"], []
        )

    # Check org role
    role = _org_role(ctx.db, ctx.user_id, ctx.organization_id)
    if role and _role_allows_org_action(ctx.db, role, action_key):
        return AccessDecision(True, role.value, ["role_allows"], [])

    return AccessDecision(
        False,
        role.value if role else None,
        ["role_denied" if role else "no_org_membership"],
        [],
    )


def authorize_team_action(
    ctx: AuthContext, team_id: uuid.UUID, action_key: str
) -> AccessDecision:
    """Authorize a team-level action."""
    # ent_ok, cap_fails = _entitlements_ok(ctx.db, ctx.organization_id, action_key)
    # if not ent_ok:
    #     return AccessDecision(False, None, ["plan_denied"], cap_fails)

    # TODO - doesn't this get rid of the need for super_admin in any of the role_action_allow_* tables? If so, is this desirable?
    # Super admins bypass role checks
    if is_super_admin(ctx.db, ctx.user_id, ctx.organization_id):
        return AccessDecision(True, TeamRole.team_admin.value, ["org_super_admin"], [])

    role = _team_role(ctx.db, team_id, ctx.user_id, ctx.organization_id)
    if role and _role_allows_team_action(ctx.db, role, action_key):
        return AccessDecision(True, role.value, ["role_allows"], [])

    return AccessDecision(
        False,
        role.value if role else None,
        ["role_denied" if role else "no_team_membership"],
        [],
    )


def authorize_super_admin(
    ctx: AuthContext, user_id: uuid.UUID, organization_id: str
) -> AccessDecision:
    if is_super_admin(ctx, user_id, organization_id):
        return AccessDecision(
            True, OrgRole.org_super_admin.value, ["org_super_admin"], []
        )
    return AccessDecision(False, OrgRole.org_super_admin.value, ["org_super_admin"], [])


# def enforce_limit(
#     db: Session,
#     organization_id: str,
#     capability_key: str,
#     current: int
# ) -> bool:
#     """Check if current usage is within limit.
#
#     Returns True if within limit, False if limit exceeded.
#     """
#     value = _cap_value(db, organization_id, capability_key)
#     if not isinstance(value, int):
#         return True  # No limit set
#     return current < value
