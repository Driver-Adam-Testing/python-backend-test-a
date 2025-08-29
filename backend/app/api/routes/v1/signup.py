import re
import uuid
from typing import Any
import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.services.auth0_service import Auth0Service

import time
from datetime import datetime, timezone
import httpx
from disposable_email_domains import blocklist

# Set up logger
logger = logging.getLogger(__name__)


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


def _verify_turnstile(token: str, remote_ip: str | None) -> dict[str, Any]:
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

    ts = j.get("challenge_ts")
    if ts:
        issued = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp()
        if time.time() - issued > settings.TURNSTILE_MAX_AGE_SEC:
            raise HTTPException(status_code=403, detail="Bot check too old")

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

    # 0c) Check if email already exists - but don't reveal this information to prevent user enumeration
    existing_users = service.find_users_by_email(str(request.email))
    if existing_users:
        # Log the attempt for monitoring but don't reveal the email exists
        logger.info(f"Signup attempt with existing email: {request.email} from IP: {remote_ip}")
        # Return success to prevent user enumeration
        return SignupResponse(
            organization_id="",
            organization_name="",
            invitation_id=None,
            message="If an account with this email exists, you will receive a sign-in link shortly."
        )

    # 1) Create a new organization per signup
    org_name = _generate_org_slug_from_email(request.email)
    org = service.create_organization(
        name=org_name,
        display_name=request.display_name or str(request.email),
        metadata={"self_service": "true"},
    )

    # 1b) Enable Username-Password-Authentication connection on the org
    # This connection is cached on first request, so we can safely use it
    conn_id = service.get_username_password_connection_id()
    service.enable_connection_for_organization(org_id=org["id"], connection_id=conn_id)

    # 2) Assign Admin role only. Resolve by name; error if missing.
    # This role is cached on first request, so we can safely use it
    admin_role_id = service.get_admin_role_id()
    role_ids: list[str] | None = [admin_role_id]

    try:
        invite = service.invite_email_to_organization(
            org_id=org["id"], email=request.email, roles=role_ids, inviter_name="System"
        )
    except Exception:
        # Cleanup org on failure
        try:
            service.delete_organization(org["id"])
            logger.info(f"Successfully cleaned up organization {org['id']} after invitation failure")
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup organization {org['id']} after invitation failure", exc_info=True)
        raise

    return SignupResponse(
        organization_id=org["id"],
        organization_name=org["name"],
        invitation_id=invite["id"],
        message="Organization created and invitation sent.",
    )


