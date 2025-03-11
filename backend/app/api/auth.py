import json
from collections.abc import Callable
from typing import Annotated, Any
from urllib.request import urlopen

import jwt
from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from jwt.algorithms import RSAAlgorithm
from pydantic import BaseModel, Field
from shared.utils.decorators import expiring_cache
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

ALGORITHMS = ["RS256"]
ORG_MANAGER = "organization:management"
CONTENT_EDITOR = "content:editor"
CONTENT_READONLY = "content:readonly"
USAGE_CREDITOR = "usage_credit:management"
SUBSCRIPTION_MANAGER = "subscription:management"
GIT_PROVIDER_MANAGER = "git_provider:management"


@expiring_cache(3600)
def get_jwks() -> dict:
    """
    We cache this for an hour so we don't have to hit the Auth0 API for every request.
    The keys will rotate, so we don't want to cache indefinitely for security reasons.
    """
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    response = urlopen(jwks_url)
    return json.loads(response.read())


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


def verify_token(token: str) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    jwks = get_jwks()
    rsa_key = get_rsa_key(jwks, unverified_header["kid"])
    if not rsa_key:
        raise HTTPException(status_code=401, detail="Unable to find appropriate key")

    public_key = RSAAlgorithm.from_jwk(json.dumps(rsa_key))
    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=ALGORITHMS,
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


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

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> JSONResponse | Response:
        if (
            request.method in ["GET", "POST"]
            and request.url.path in UNPROTECTED_PATHS
            or request.method == "OPTIONS"
        ):
            pass
        else:
            auth_header = request.headers.get("Authorization")
            if auth_header is None or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401, content="Missing or malformed Authorization header"
                )
            token = auth_header[len("Bearer ") :]
            try:
                payload = verify_token(token)
                request.state.token_payload = payload
            except Exception:
                return JSONResponse(status_code=401, content="Unauthorized")

        response = await call_next(request)
        return response


class User(BaseModel):
    organization_id: str = Field(..., alias="org_id")
    organization_display_name: str = Field(..., alias="org_name")
    user_id: str = Field(..., alias="sub")
    issuer: str = Field(..., alias="iss")
    subject: str = Field(..., alias="sub")
    audience: list[str] | str = Field(..., alias="aud")
    issued_at: int = Field(..., alias="iat")
    expiration: int = Field(..., alias="exp")
    scope: str = Field(..., alias="scope")
    organization_name: str = Field(..., alias="org_name")
    authorized_party: str = Field(..., alias="azp")
    permissions: list[str] = Field()
    email: str = Field(..., alias="user_email")
    full_name: str = Field(..., alias="user_full_name")


class M2M(BaseModel):
    issuer: str = Field(..., alias="iss")
    subject: str = Field(..., alias="sub")
    audience: list[str] | str = Field(..., alias="aud")
    issued_at: int = Field(..., alias="iat")
    expiration: int = Field(..., alias="exp")
    authorized_party: str = Field(..., alias="azp")


def get_token_payload(request: Request) -> dict:
    # The only way this is populated is after it has been validated
    return request.state.token_payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_payload: dict = Depends(get_token_payload),
) -> User | None:
    if token_payload.get("userId") is not None:
        return User(**token_payload)
    return None


def get_current_m2m(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_payload: dict = Depends(get_token_payload),
) -> M2M | None:
    if token_payload.get("userId") is None:
        return M2M(**token_payload)
    return None


def require_permission(permission: str) -> Callable[[dict[str, Any]], bool]:
    def permission_dependency(
        user: dict[str, Any] = Depends(get_current_user),
        token_payload: dict[str, Any] = Depends(get_token_payload),
    ) -> bool:
        permissions = token_payload.get("permissions", [])
        if permission not in permissions:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )
        return True

    return permission_dependency


UserToken = Annotated[User, Depends(get_current_user)]
M2MToken = Annotated[M2M, Depends(get_current_m2m)]

ContentEditorPermission = Depends(require_permission(CONTENT_EDITOR))
ContentReadonlyPermission = Depends(require_permission(CONTENT_READONLY))
OrgManagerPermission = Depends(require_permission(ORG_MANAGER))
UsageCreditPermission = Depends(require_permission(USAGE_CREDITOR))
SubscriptionManagerPermission = Depends(require_permission(SUBSCRIPTION_MANAGER))
GitProviderManagerPermission = Depends(require_permission(GIT_PROVIDER_MANAGER))
