from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Annotated, Any
from urllib.request import urlopen

import jwt
from database.models_v2 import ApiKey
from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from jwt.algorithms import RSAAlgorithm
from pydantic import BaseModel, Field
from shared.utils.decorators import expiring_cache
from sqlmodel import select
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

if TYPE_CHECKING:
    from collections.abc import Callable

# ---------------------------------------------------------------------
#  CONSTANTS
# ---------------------------------------------------------------------
ALGORITHMS = ["RS256"]

ORG_MANAGER = "organization:management"
CONTENT_EDITOR = "content:editor"
CONTENT_READONLY = "content:readonly"
USAGE_CREDITOR = "usage_credit:management"
SUBSCRIPTION_MANAGER = "subscription:management"
GIT_PROVIDER_MANAGER = "git_provider:management"

UNPROTECTED_PATHS = [
    "/login",
    "/api/v1/healthcheck/",
    "/docs",
    "/api/v1/openapi.json",
    "/redoc",
    "/api/v1/sandbox/apollo-sandbox/",
    "/api/v1/git-provider/github/webhook",
    "/api/v1/git-provider/github/callback",
    "/api/v1/git-provider/app/callback",
    "/api/v1/git-provider/app/webhook",
]

JWT_SCHEME = HTTPBearer(auto_error=False)  # we handle errors ourselves
API_KEY_HEADER_NAME = "X-API-Key"


@expiring_cache(3600)
def get_jwks() -> dict:
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    return json.loads(urlopen(jwks_url).read())


def get_rsa_key(jwks: dict, kid: str) -> dict:
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
    return {}


def verify_jwt(token: str) -> dict:
    """Decode & verify Auth0 RS256 JWT."""
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = get_rsa_key(get_jwks(), unverified_header["kid"])
    if not rsa_key:
        raise HTTPException(status_code=401, detail="Unable to find appropriate key")

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
        raise HTTPException(status_code=401, detail="Unauthorized")


def verify_api_key(key: str) -> dict:
    """
    Look up the ApiKey row with the supplied raw key, and build a payload resembling Auth0's so the User model still works.
    """
    from database.db import get_session

    with get_session() as db:
        key = db.exec(select(ApiKey).where(ApiKey.salted_key == key)).one_or_none()
        if key:
            # Build a payload resembling Auth0's so the User model still works
            now = int(time.time())
            return {
                "org_id": key.organization_id,
                "org_name": "",  # fill if you have it
                "sub": key.user_id,
                "iss": "api_key",
                "aud": [],
                "iat": now,
                "exp": now + 10 * 365 * 24 * 3600,  # arbitrary distant future
                "scope": "",
                "azp": "",
                "permissions": [],
                "user_email": "",
                "user_full_name": "",
            }
    raise HTTPException(status_code=401, detail="Invalid API key")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> JSONResponse | Response:
        if (
            request.method in ("GET", "POST") and request.url.path in UNPROTECTED_PATHS
        ) or request.method == "OPTIONS":
            # health checks & other public routes
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get(API_KEY_HEADER_NAME)

        try:
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[len("Bearer ") :]
                request.state.token_payload = verify_jwt(token)

            elif api_key_header:
                request.state.token_payload = verify_api_key(api_key_header)

            else:
                return JSONResponse(
                    status_code=401, content="Missing authentication credentials"
                )

        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)

        # validated → continue to route
        return await call_next(request)


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
    authorized_party: str = Field(..., alias="azp")


# ---------------------------------------------------------------------
def get_token_payload(request: Request) -> dict:
    return request.state.token_payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(JWT_SCHEME),
    token_payload: dict = Depends(get_token_payload),
) -> User | None:
    # For both JWT and API-key payloads we set "sub" → user id
    if token_payload.get("sub"):
        return User(**token_payload)
    return None


def get_current_m2m(
    credentials: HTTPAuthorizationCredentials | None = Depends(JWT_SCHEME),
    token_payload: dict = Depends(get_token_payload),
) -> M2M | None:
    # Treat payloads that have *no* userId/sub as M2M
    if not token_payload.get("sub"):
        return M2M(**token_payload)
    return None


def require_permission(permission: str) -> Callable[[dict[str, Any]], bool]:
    def dependency(
        user: dict[str, Any] = Depends(get_current_user),
        token_payload: dict[str, Any] = Depends(get_token_payload),
    ) -> bool:
        if permission not in token_payload.get("permissions", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return True

    return dependency


UserToken = Annotated[User, Depends(get_current_user)]
M2MToken = Annotated[M2M, Depends(get_current_m2m)]
ContentEditorPermission = Depends(require_permission(CONTENT_EDITOR))
ContentReadonlyPermission = Depends(require_permission(CONTENT_READONLY))
OrgManagerPermission = Depends(require_permission(ORG_MANAGER))
UsageCreditPermission = Depends(require_permission(USAGE_CREDITOR))
SubscriptionManagerPermission = Depends(require_permission(SUBSCRIPTION_MANAGER))
GitProviderManagerPermission = Depends(require_permission(GIT_PROVIDER_MANAGER))
