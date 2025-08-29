import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.services.auth0_service import Auth0Service

import time
from datetime import datetime, timezone
import httpx
from disposable_email_domains import blocklist


router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    # Optional org display name to show in invitations
    display_name: str | None = None
    captcha_token: str


class SignupResponse(BaseModel):
    organization_id: str
    organization_name: str
    invitation_id: str | None = None
    message: str


def _generate_org_slug_from_email(email: str) -> str:
    local = email.split("@")[0]
    safe = re.sub(r"[^a-z0-9]+", "-", local.lower()).strip("-")
    unique_suffix = uuid.uuid4().hex[:6]
    return f"org-{safe}-{unique_suffix}" if safe else f"org-{unique_suffix}"


def _verify_turnstile(token: str, remote_ip: str | None = None) -> dict[str, Any]:
    """Verify Cloudflare Turnstile token; enforce hostname/action/freshness if configured."""
    if not settings.TURNSTILE_SECRET:
        # Not configured (e.g., local dev) → skip verification
        return {"success": True, "skipped": True}

    data: dict[str, str] = {"secret": settings.TURNSTILE_SECRET, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip

    with httpx.Client(timeout=10) as client:
        r = client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    j = r.json()

    if not j.get("success"):
        raise HTTPException(status_code=403, detail=f"Bot check failed: {j.get('error-codes')}")

    if settings.TURNSTILE_EXPECTED_HOSTNAME and j.get("hostname") != settings.TURNSTILE_EXPECTED_HOSTNAME:
        raise HTTPException(status_code=403, detail="Bot check hostname mismatch")

    if j.get("action") and j["action"] != "signup":
        raise HTTPException(status_code=403, detail="Bot check action mismatch")

    try:
        ts = j.get("challenge_ts")
        if ts:
            issued = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp()
            if time.time() - issued > settings.TURNSTILE_MAX_AGE_SEC:
                raise HTTPException(status_code=403, detail="Bot check too old")
    except HTTPException:
        raise
    except Exception:
        pass

    return j

def _is_disposable(email: str) -> bool:
    domain = email.split("@", 1)[-1].lower()
    return domain in blocklist


@router.post("", summary="Create org and invite email")
def signup(req: Request, request: SignupRequest) -> SignupResponse:
    service = Auth0Service()

    # 0) Disposable email check using disposable_email_domains blocklist
    if _is_disposable(str(request.email)):
        raise HTTPException(status_code=400, detail="Use a non-disposable email address.")

    # 0b) Turnstile gate
    remote_ip = req.client.host if req.client else None
    _verify_turnstile(request.captcha_token, remote_ip=remote_ip)

    # 0c) If this email already exists in Auth0, do not create a new org
    try:
        existing_users = service.find_users_by_email(str(request.email))
        if existing_users:
            raise HTTPException(
                status_code=409,
                detail="A Driver account with this email already exists. Sign in or check your inbox for an invitation.",
            )
    except HTTPException:
        raise
    except Exception:
        # Non-fatal: proceed, but prefer safety. If lookup fails we still allow signups.
        pass


    # 1) Create a new organization per signup
    org_name = _generate_org_slug_from_email(request.email)
    try:
        org = service.create_organization(
            name=org_name,
            display_name=request.display_name or str(request.email),
            metadata={"self_service": "true"},
        )
    except Exception as e:  # pragma: no cover - pass through as HTTP error
        raise HTTPException(status_code=500, detail="Failed to create organization") from e

    # 1b) Ensure Username-Password-Authentication connection is enabled on the org
    try:
        conn_id = service.get_connection_id_by_name("Username-Password-Authentication")
        if not conn_id:
            raise HTTPException(status_code=500, detail="Auth0 connection not found: Username-Password-Authentication")
        service.enable_connection_for_organization(org_id=org["id"], connection_id=conn_id)
    except Exception as e:
        # Cleanup org on failure
        try:
            service.delete_organization(org["id"])
        except Exception:
            pass
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to enable connection for organization") from e

    # 2) Assign Admin role only. Resolve by name; fallback to env; error if missing.
    admin_role_id = service.get_role_id_by_name("Admin")
    if not admin_role_id and settings.AUTH0_ORG_ADMIN_ROLE_ID:
        admin_role_id = settings.AUTH0_ORG_ADMIN_ROLE_ID
    if not admin_role_id:
        # Cleanup org on failure
        try:
            service.delete_organization(org["id"])
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=(
                "Admin role not found in Auth0. Create an 'Admin' role or set AUTH0_ORG_ADMIN_ROLE_ID."
            ),
        )
    role_ids: list[str] | None = [admin_role_id]

    try:
        invite = service.invite_email_to_organization(
            org_id=org["id"], email=request.email, roles=role_ids, inviter_name="System"
        )
    except Exception as e:
        # Cleanup org on failure
        try:
            service.delete_organization(org["id"])
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to create invitation") from e

    return SignupResponse(
        organization_id=org["id"],
        organization_name=org["name"],
        invitation_id=invite.get("id"),
        message="Organization created and invitation sent.",
    )


