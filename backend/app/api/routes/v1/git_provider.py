from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Response, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.status import HTTP_302_FOUND
from app.core.config import settings
from app.utils.gh_ops import exchange_code_for_token, download_and_upload_repo
from app.utils.aws_secrets_manager import format_secret_key, write_secret, read_secret
from pydantic import BaseModel
import base64
import json
from pydantic import BaseModel
from app.api.session import CurrentSession
from app.api.auth import CurrentUser
import hashlib
import hmac

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
async def git_provider_callback(provider: str, code: str, state: str, installation_id: str, request: Request,
                                response: Response):
    if provider != "github":
        raise HTTPException(status_code=400, detail="Bad request")

    if not code:
        raise HTTPException(status_code=400, detail="Bad request")

    state_bytes = base64.b64decode(state)
    state_str = state_bytes.decode('utf-8')
    state_dict = json.loads(state_str)

    org_id, user_id = state_dict["org_id"], state_dict["user_id"]
    secret_key = format_secret_key(org_id, user_id, provider)
    token_data = await exchange_code_for_token(code)
    # store access token in aws secret manager
    # token_data['installation_id'] = installation_id
    secret_value = json.dumps(token_data)
    # secret_value = json.dumps({'token_data': token_data, 'installation_id': installation_id})
    write_secret(secret_key, secret_value)
    value = read_secret(secret_key)
    if value is not None:
        print('Secret stored successfully')
    content = "<html><body><script>window.close();</script></body></html>"
    return Response(content=content, media_type="text/html")


class GitRepository(BaseModel):
    workspace_id: str
    provider_name: str
    repo_name: str
    org: str
    last_updated: datetime
    metadata: dict


# endpoint to clone repo and pipe to s3
@router.post("/{provider}/clone-repo")
async def clone_repo(session: CurrentSession, current_user: CurrentUser, provider: str, repo: GitRepository):
    secret_key = format_secret_key(current_user.organization_id, current_user.user_id, provider)
    value = read_secret(secret_key)
    token = None
    upload_complete = False
    if value is not None:
        s = value['SecretString']
        secret_sauce = json.loads(s)
        token = secret_sauce['access_token']
        upload_complete = await download_and_upload_repo(
            repo.org,
            current_user.user_id,
            current_user.organization_id,
            repo.workspace_id,
            repo.repo_name,
            repo.metadata['clone_url'],
            token)

    if upload_complete is True:
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"message": "Upload complete"})
    else:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Upload failed"})


def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")


@router.post("/{provider}/webhook")
async def webhook(provider: str, request: Request):
    # Ensure the request body is read as bytes for signature verification
    body_bytes = await request.body()  # Get the raw request body as bytes
    body = await request.json()  # Parse the JSON body for further processing
    github_event = request.headers.get('x-github-event', '')
    signature_header = request.headers.get('x-hub-signature-256', '')

    # Verify the GitHub signature
    secret_token = settings.GH_WEBHOOK_SECRET  # Ensure you have this configured in your settings or environment
    try:
        verify_signature(body_bytes, secret_token, signature_header)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    # TODO handle install event
    # TODO handle uninstall event
    # TODO handle revoke event

    # Respond to indicate that the delivery was successfully received
    if github_event == 'issues':
        action = body.get('action', '')
        if action == 'opened':
            print(f"An issue was opened with this title: {body['issue']['title']}")
        elif action == 'closed':
            print(f"An issue was closed by {body['issue']['user']['login']}")
        else:
            print(f"Unhandled action for the issue event: {action}")
    elif github_event == 'ping':
        print('GitHub sent the ping event')
    else:
        print(f"Unhandled event: {github_event}")
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"message": "Accepted"})
