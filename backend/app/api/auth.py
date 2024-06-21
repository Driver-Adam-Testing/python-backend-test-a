import json
from typing import Annotated
from urllib.request import urlopen

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

ALGORITHMS = ["RS256"]


def get_jwks() -> dict:
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
    rsa_key = get_rsa_key(get_jwks(), unverified_header["kid"])
    if not rsa_key:
        raise JWTError("Unable to find appropriate key")
    payload = jwt.decode(
        token,
        rsa_key,
        algorithms=ALGORITHMS,
        audience=settings.AUTH0_AUDIENCE,
        issuer=f"https://{settings.AUTH0_DOMAIN}/",
    )
    return payload


UNPROTECTED_PATHS = [
    "/login",
    "/api/v1/healthcheck/",
    "/docs",
    "/api/v1/openapi.json",
    "/redoc",
    "/api/v1/sandbox/apollo-sandbox/",
    "/api/v1/git-provider/github/auth",
    "/api/v1/git-provider/github/install",
    "/api/v1/git-provider/github/webhook",
    "/api/v1/git-provider/github/callback",
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.method in ["GET", "POST"] and request.url.path in UNPROTECTED_PATHS:
                pass
            elif request.method == "OPTIONS":
                pass
            else:
                auth_header = request.headers.get("Authorization")
                if auth_header is None or not auth_header.startswith("Bearer "):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Malformed or missing Authorization header",
                    )
                else:
                    token = auth_header[len("Bearer ") :]
                    try:
                        payload = verify_token(token)
                        request.state.token_payload = payload
                    except Exception as e:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
                        )
            response = await call_next(request)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code, content={"detail": exc.detail}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": str(e)},
            )
        return response


security = HTTPBearer()


class User(BaseModel):
    organization_id: str = Field(..., alias="orgId")
    organization_display_name: str = Field(..., alias="org_display_name")
    user_id: str = Field(..., alias="userId")
    is_service_account: bool = Field(..., alias="isServiceAccount")
    issuer: str = Field(..., alias="iss")
    subject: str = Field(..., alias="sub")
    audience: list[str] = Field(..., alias="aud")
    issued_at: int = Field(..., alias="iat")
    expiration: int = Field(..., alias="exp")
    scope: str = Field(..., alias="scope")
    organization_name: str = Field(..., alias="org_name")
    authorized_party: str = Field(..., alias="azp")

class M2M(BaseModel):
    issuer: str = Field(..., alias="iss")
    subject: str = Field(..., alias="sub")
    audience: list[str] = Field(..., alias="aud")
    issued_at: int = Field(..., alias="iat")
    expiration: int = Field(..., alias="exp")
    authorized_party: str = Field(..., alias="azp")


def get_token_payload(request: Request) -> dict:
    return request.state.token_payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_payload: dict = Depends(get_token_payload),
) -> User:
    return User(**token_payload)

def get_current_m2m(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_payload: dict = Depends(get_token_payload),
) -> M2M:
    return M2M(**token_payload)


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentToken = Annotated[M2M, Depends(get_current_m2m)]