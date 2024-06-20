from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from app.core.config import settings
from app.utils.gh_ops import exchange_code_for_token
from app.utils.aws_secrets_manager import format_secret_key, write_secret, read_secret
from pydantic import BaseModel
import base64
import json

router = APIRouter()


class OkResponse(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"


@router.get("/{provider}/auth")
async def provider_auth(request: Request, response: Response, provider: str):
    client_id = settings.GH_CLIENT_ID
    redirect_uri = settings.GH_REDIRECT_URI
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&scope=repo&redirect_uri={redirect_uri}"
    print(github_auth_url)
    response.status_code = HTTP_302_FOUND
    response.headers["Location"] = github_auth_url


@router.get("/{provider}/install", response_model=OkResponse)
def install_url(org_id: str, user_id: str):
    redirect_uri = settings.GH_REDIRECT_URI
    state_dict = json.dumps({"org_id": org_id, "user_id": user_id})
    state = base64.b64encode(state_dict.encode('utf-8')).decode('utf-8')
    install_link = f"https://github.com/apps/driverai-gh-demo/installations/new?state={state}&redirect_uri={redirect_uri}"
    return OkResponse(status=install_link)


@router.get("/{provider}/callback", response_model=OkResponse)
async def git_provider_callback(provider: str, code: str, state: str, request: Request, response: Response):
    if provider != "github":
        raise HTTPException(status_code=400, detail="Bad request")

    if not code:
        raise HTTPException(status_code=400, detail="Bad request")

    try:
        state_bytes = base64.b64decode(state)
        state_str = state_bytes.decode('utf-8')
        state_dict = json.loads(state_str)

        org_id, user_id = state_dict["org_id"], state_dict["user_id"]
        secret_key = format_secret_key(org_id, user_id, provider)
        token_data = await exchange_code_for_token(code)
        # store access token in aws secret manager
        secret_value = json.dumps(token_data)
        write_secret(secret_key, secret_value)
        value = read_secret(secret_key)
        if value is not None:
            print('Secret stored successfully')
            return OkResponse(status="OK")
        else:
            print('Failed to store secret')
            raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as error:
        print(error)
        raise HTTPException(status_code=500, detail="Internal Server Error")
