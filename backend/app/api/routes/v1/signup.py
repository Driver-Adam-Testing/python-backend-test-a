import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.services.auth0_service import Auth0Service


router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    # Optional org display name to show in invitations
    display_name: str | None = None


class SignupResponse(BaseModel):
    organization_id: str
    organization_name: str
    invitation_id: str | None = None
    invitation_url: str | None = None
    message: str


def _generate_org_slug_from_email(email: str) -> str:
    local = email.split("@")[0]
    safe = re.sub(r"[^a-z0-9]+", "-", local.lower()).strip("-")
    unique_suffix = uuid.uuid4().hex[:8]
    return f"org-{safe}-{unique_suffix}" if safe else f"org-{unique_suffix}"


@router.post("", include_in_schema=False)
@router.post("/", summary="Create org and invite email")
def signup(request: SignupRequest) -> SignupResponse:
    service = Auth0Service()

    # 1) Create a new organization per signup
    org_name = _generate_org_slug_from_email(request.email)
    try:
        org = service.create_organization(
            name=org_name, display_name=request.display_name or f"User - {request.email}"
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
            org_id=org["id"], email=request.email, roles=role_ids, inviter_name="System", send_invitation_email=False
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
        invitation_url=invite.get("invitation_url"),
        message="Organization created and invitation sent.",
    )


