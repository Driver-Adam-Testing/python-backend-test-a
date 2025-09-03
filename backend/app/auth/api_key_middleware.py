from datetime import datetime
from zoneinfo import ZoneInfo

from app.auth.api_key_common import create_api_key_payload
from app.auth.models import User
from app.services.auth0_service import Auth0Service
from cachetools import TTLCache, cached
from database.db import get_session
from database.models import ApiKey
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlmodel import select

_auth0 = Auth0Service()


def _is_member_of_org(user_id: str, org_id: str) -> bool:
    """
    Ask Auth0 Management API whether *user_id* belongs to *org_id*.
    Cached 1 hour to avoid rate-limits.
    """
    orgs = dict(
        _auth0.list_user_organizations(
            user=User(
                org_id=org_id,
                sub=user_id,
                iss="internal",
                aud=[],
                iat=0,
                exp=0,
            )
        )
    )
    return any(o["id"] == org_id for o in orgs["organizations"])


@cached(cache=TTLCache(maxsize=1000, ttl=600))  # 1000 Users get a cache of 5 minutes
def verify_api_key(raw_key: str) -> dict:
    """
    Validate *raw_key* against the v2_api_key table and return a
    JWT-shaped payload so downstream code can treat it like a user JWT.
    """

    with get_session() as db:
        api_key: ApiKey | None = db.exec(
            select(ApiKey).where(ApiKey.key == raw_key)
        ).one_or_none()

        if not api_key:
            raise HTTPException(401, "Invalid API key")
        # -------- new: Auth0 membership check --------
        if not _is_member_of_org(api_key.user_id, api_key.organization_id):
            raise HTTPException(401, "User does not belong to this organization")
        api_key.last_used_at = datetime.now(ZoneInfo("UTC"))
        db.add(api_key)
        db.commit()
        return create_api_key_payload(api_key)


API_KEY_HEADER_NAME = "X-API-Key"


API_KEY_SCHEME = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def require_api_key(key: str | None = Depends(API_KEY_SCHEME)) -> dict:
    """Dependency: assert request carries a valid X-API-Key header."""
    if not key:
        raise HTTPException(401, "Missing X-API-Key header")
    return User(**verify_api_key(key))
