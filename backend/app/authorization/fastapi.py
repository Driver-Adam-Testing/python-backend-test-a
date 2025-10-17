"""Authorization helpers for RBAC."""

import uuid

from app.auth.models import User
from app.authorization.core import (
    AccessDecision,
    AuthContext,
    authorize_asset_action,
    authorize_org_action,
)
from fastapi import HTTPException
from sqlmodel import Session


def _build_auth_context(db: Session, user: User) -> AuthContext:
    """Build authorization context."""
    return AuthContext(
        db=db,
        user_id=user.user_id,
        organization_id=user.organization_id,
    )


def check_org_action(db: Session, user: User, action_key: str) -> AccessDecision:
    """Check org action authorization and return decision."""
    ctx = _build_auth_context(db, user)
    return authorize_org_action(ctx, action_key)


def check_asset_action(
    db: Session, user: User, asset_id: uuid.UUID, action_key: str
) -> AccessDecision:
    """Check asset action authorization and return decision."""
    ctx = _build_auth_context(db, user)
    return authorize_asset_action(ctx, asset_id, action_key)


def enforce_org_action(db: Session, user: User, action_key: str) -> None:
    decision = check_org_action(db, user, action_key)
    if not decision.allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "insufficient_permissions",
                "action": action_key,
                "reasons": decision.reasons,
            },
        )


def enforce_asset_action(
    db: Session, user: User, asset_id: uuid.UUID, action_key: str
) -> None:
    """Check asset action and raise HTTPException(403) if denied.

    Example:
        @router.put("/primary_assets/{primary_asset_id}")
        def update_asset(session: CurrentSession, user: UserToken, primary_asset_id: UUID):
            enforce_asset_action(session, user, primary_asset_id, "primary_asset.update")
            # ... rest of implementation
    """
    decision = check_asset_action(db, user, asset_id, action_key)
    if not decision.allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "insufficient_permissions",
                "action": action_key,
                "asset_id": str(asset_id),
                "reasons": decision.reasons,
            },
        )
