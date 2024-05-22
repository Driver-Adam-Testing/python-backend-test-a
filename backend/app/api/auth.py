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

AUTH0_DOMAIN = "driverai.us.auth0.com"
API_IDENTIFIER = "https://driveraiapi.ngrok.io"
ALGORITHMS = ["RS256"]


def get_jwks() -> dict:
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
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
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise Exception("Invalid header. Use an RS256 signed JWT Access Token")

    rsa_key = get_rsa_key(get_jwks(), unverified_header["kid"])
    if not rsa_key:
        raise Exception("Unable to find appropriate key")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_IDENTIFIER,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload
    except JWTError:
        raise Exception("Token invalid or expired")


def get_token_payload(request: Request) -> dict:
    return request.state.token_payload


GetTokenPayload = Annotated[dict, Depends(get_token_payload)]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.url.path not in (
                "/login",
                "/docs",
                "/api/v1/openapi.json",
                "/redoc",
            ):
                auth_header = request.headers.get("Authorization")
                if auth_header is None or not auth_header.startswith("Bearer "):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_payload: dict = Depends(get_token_payload),
):
    return User(**token_payload)


CurrentUser = Annotated[User, Depends(get_current_user)]
