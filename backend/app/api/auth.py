"""
auth.py - authentication helpers for Driver FastAPI apps.

Responsibilities
----------------
* Verify & decode Auth0 JWTs (RS256).
* Verify API keys stored in the v2_api_key table.
* Provide FastAPI dependencies:
    * `require_jwt`
    * `require_api_key`
* Helper Pydantic models (`User`, `M2M`).
* Permission dependency factory (`require_permission`).

NOTE: Path based auth enforcement moved to router level dependencies.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Annotated, Any
from urllib.request import urlopen

import jwt
from database.models_v2 import ApiKey
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from jwt.algorithms import RSAAlgorithm
from pydantic import BaseModel, Field
from shared.utils.decorators import expiring_cache
from sqlmodel import select

from app.core.config import settings

if TYPE_CHECKING:
    from collections.abc import Callable

ALGORITHMS = ["RS256"]

# Permission strings we embed in JWTs
ORG_MANAGER = "organization:management"
CONTENT_EDITOR = "content:editor"
CONTENT_READONLY = "content:readonly"
USAGE_CREDITOR = "usage_credit:management"
SUBSCRIPTION_MANAGER = "subscription:management"
GIT_PROVIDER_MANAGER = "git_provider:management"

# Paths that do NOT require authentication
UNPROTECTED_PATHS = {
    "/login",
    "/studio/v1/healthcheck/",
    "/docs",
    "/studio/v1/openapi.json",
    "/redoc",
    "/studio/v1/sandbox/apollo-sandbox/",
    "/studio/v1/git-provider/github/webhook",
    "/studio/v1/git-provider/github/callback",
    "/studio/v1/git-provider/app/callback",
    "/studio/v1/git-provider/app/webhook",
}

API_KEY_HEADER_NAME = "X-API-Key"

_jwt_scheme = HTTPBearer(auto_error=False)
_api_key_scheme = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


class User(BaseModel):
    organization_id: str = Field(..., alias="org_id")
    organization_display_name: str | None = Field("", alias="org_name")
    user_id: str = Field(..., alias="sub")
    issuer: str = Field(..., alias="iss")
    subject: str = Field(..., alias="sub")
    audience: list[str] | str = Field(..., alias="aud")
    issued_at: int = Field(..., alias="iat")
    expiration: int = Field(..., alias="exp")
    scope: str = Field("", alias="scope")
    authorized_party: str = Field("", alias="azp")
    permissions: list[str] = Field(default_factory=list)
    email: str | None = Field("", alias="user_email")
    full_name: str | None = Field("", alias="user_full_name")


class M2M(BaseModel):
    issuer: str = Field(..., alias="iss")
    subject: str = Field(..., alias="sub")
    audience: list[str] | str = Field(..., alias="aud")
    issued_at: int = Field(..., alias="iat")
    expiration: int = Field(..., alias="exp")
    authorized_party: str = Field("", alias="azp")


@expiring_cache(3600)
def get_jwks() -> dict:
    """Fetch Auth0 JWKS (memoised for 1 hour)."""
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    return json.loads(urlopen(jwks_url).read())


def _get_rsa_key(jwks: dict, kid: str) -> dict:
    """Return the JWK that matches *kid* (or {})."""
    return next((k for k in jwks["keys"] if k["kid"] == kid), {})


def verify_jwt(token: str) -> dict:
    """
    Verify an Auth0 RS256 JWT and return its payload.

    Raises
    ------
    HTTPException(401)
        If the token is invalid or cannot be verified.
    """

    header = jwt.get_unverified_header(token)
    rsa_key = _get_rsa_key(get_jwks(), header["kid"])
    if not rsa_key:
        raise HTTPException(401, "Unable to find appropriate key")

    try:
        public_key = RSAAlgorithm.from_jwk(json.dumps(rsa_key))
        return jwt.decode(
            token,
            public_key,
            algorithms=ALGORITHMS,
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
    except PyJWTError:
        raise HTTPException(401, "Unauthorized")


def verify_api_key(raw_key: str) -> dict:
    """
    Validate *raw_key* against the v2_api_key table and return a
    JWT-shaped payload so downstream code can treat it like a user JWT.
    """
    from database.db import get_session

    with get_session() as db:
        rec: ApiKey | None = db.exec(
            select(ApiKey).where(ApiKey.key == raw_key)
        ).one_or_none()

        if not rec:
            raise HTTPException(401, "Invalid API key")

        now = int(time.time())
        # Shape chosen to match Auth0 tokens consumed elsewhere
        # TODO: Either ensure that this user exists in Auth0 (or use a cache)
        return {
            "org_id": rec.organization_id,
            "org_name": "",  # TODO: populate when available
            "sub": rec.user_id,
            "iss": "api_key",
            "aud": [],
            "iat": now,
            "exp": now + 10 * 365 * 24 * 3600,  # 10 years
            "scope": "",
            "azp": "",
            "permissions": [],
            "user_email": "",
            "user_full_name": "",
        }


def require_jwt(
    creds: HTTPAuthorizationCredentials | None = Depends(_jwt_scheme),
) -> dict:
    """Dependency: assert request carries a valid Bearer token."""
    if not creds or not creds.credentials:
        raise HTTPException(401, "Missing Bearer token")
    return User(**verify_jwt(creds.credentials))


def require_api_key(key: str | None = Depends(_api_key_scheme)) -> dict:
    """Dependency: assert request carries a valid X-API-Key header."""
    if not key:
        raise HTTPException(401, "Missing X-API-Key header")
    return User(**verify_api_key(key))


# Aliases that save typing in route signatures
UserToken = Annotated[User, Depends(require_jwt)]
M2MToken = Annotated[M2M, Depends(require_api_key)]


def require_permission(permission: str) -> Callable[[dict[str, Any]], bool]:
    """Factory that returns a dependency enforcing *permission* in JWT."""

    def dep(payload: dict[str, Any] = Depends(require_jwt)) -> bool:
        if permission not in payload.get("permissions", []):
            raise HTTPException(403, "Insufficient permissions")
        return True

    return dep


ContentEditorPermission = Depends(require_permission(CONTENT_EDITOR))
ContentReadonlyPermission = Depends(require_permission(CONTENT_READONLY))
OrgManagerPermission = Depends(require_permission(ORG_MANAGER))
UsageCreditPermission = Depends(require_permission(USAGE_CREDITOR))
SubscriptionManagerPermission = Depends(require_permission(SUBSCRIPTION_MANAGER))
GitProviderManagerPermission = Depends(require_permission(GIT_PROVIDER_MANAGER))
