import json
import logging
import os
from typing import Annotated
from urllib import parse, request

from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2AuthorizationCodeBearer,
)
from jose import jwt
from pydantic import BaseModel, Field, ValidationError
from typing_extensions import TypedDict

logger = logging.getLogger("driverai_auth0")
domain = "driverai.us.auth0.com"
algorithms = ["RS256"]
audience = "http://localhost"


class Auth0UnauthenticatedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        """Returns HTTP 401"""
        super().__init__(401, detail, **kwargs)


class Auth0UnauthorizedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        """Returns HTTP 403"""
        super().__init__(403, detail, **kwargs)


class JwksKeyDict(TypedDict):
    kid: str
    kty: str
    use: str
    n: str
    e: str


class JwksDict(TypedDict):
    keys: list[JwksKeyDict]


auth0_rule_namespace: str = os.getenv(
    "AUTH0_RULE_NAMESPACE", "https://api.driverai.com/email"
)
authcode_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://driverai.us.auth0.com/authorize?audience={audience}",
    tokenUrl="https://driverai.us.auth0.com/oauth/token",
    scopes={},
)


class Auth0User(BaseModel):
    id: str = Field(..., alias="sub")
    permissions: list[str] | None = None
    email: str | None = Field(None, alias=f"{auth0_rule_namespace}/email")  # type: ignore [literal-required]


class Auth0:
    def __init__(
        self,
        domain: str,
        api_audience: str,
        scopes: dict[str, str] | None = None,
        auth0user_model: type[Auth0User] = Auth0User,
    ):
        self.domain = domain
        self.audience = api_audience

        self.auth0_user_model = auth0user_model

        self.algorithms = ["RS256"]
        r = request.urlopen(f"https://{domain}/.well-known/jwks.json")
        self.jwks: JwksDict = json.loads(r.read())

        authorization_url_qs = parse.urlencode({"audience": api_audience})
        authorization_url = f"https://{domain}/authorize?{authorization_url_qs}"
        self.authcode_scheme = OAuth2AuthorizationCodeBearer(
            authorizationUrl=authorization_url,
            tokenUrl=f"https://{domain}/oauth/token",
            scopes=scopes or {},
        )

    async def get_user(
        self,
        creds: HTTPAuthorizationCredentials | None = Depends(
            HTTPBearer(auto_error=False)
        ),
    ) -> Auth0User | None:
        """
        Verify the Authorization: Bearer token and return the user.
        otherwise return None.
        """

        if creds is None:
            raise HTTPException(401, detail="Missing bearer token")

        token = creds.credentials
        payload: dict = {}
        try:
            unverified_header = jwt.get_unverified_header(token)

            if "kid" not in unverified_header:
                raise Auth0UnauthenticatedException(detail="Malformed token header")

            rsa_key = {}
            for key in self.jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
                    break
            if rsa_key:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=self.algorithms,
                    audience=self.audience,
                    issuer=f"https://{self.domain}/",
                )
            else:
                msg = "Invalid kid header (wrong tenant or rotated public key)"
                raise Auth0UnauthenticatedException(detail=msg)

        except jwt.ExpiredSignatureError:
            msg = "Expired token"
            raise Auth0UnauthenticatedException(detail=msg)

        except jwt.JWTClaimsError:
            msg = "Invalid token claims (wrong issuer or audience)"
            raise Auth0UnauthenticatedException(detail=msg)

        except jwt.JWTError:
            msg = "Malformed token"
            raise Auth0UnauthenticatedException(detail=msg)

        except Auth0UnauthenticatedException:
            raise

        except Exception as e:
            logger.error(f'Handled exception decoding token: "{e}"', exc_info=True)
            raise Auth0UnauthenticatedException(detail="Error decoding token")

        try:
            user = Auth0User(**payload)

            return user

        except ValidationError as e:
            logger.error(f'Handled exception parsing Auth0User: "{e}"', exc_info=True)
            raise Auth0UnauthorizedException(detail="Error parsing Auth0User")


auth = Auth0(domain="driverai.us.auth0.com", api_audience="http://localhost")


def get_current_user(
    token: str = Depends(authcode_scheme), user: Auth0User = Depends(auth.get_user)
) -> Auth0User:
    return user


CurrentUser = Annotated[Auth0User, Depends(get_current_user)]
