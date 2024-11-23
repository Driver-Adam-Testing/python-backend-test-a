import base64
import hashlib
import hmac
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.auth import ContentEditorPermission, UserToken
from app.api.session import CurrentSession
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.utils.aws_secrets_manager import format_secret_key, read_secret, write_secret
from app.utils.gh_ops import download_and_upload_repo, exchange_code_for_token

router = APIRouter()


class OkResponse(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@router.get("/{provider}/callback", response_model=OkResponse)
async def git_provider_callback(
    session: CurrentSession,
    provider: str,
    code: str,
    state: str,
    installation_id: str,
    request: Request,
    response: Response,
):
    if provider != "github":
        raise HTTPException(status_code=400, detail="Bad request")

    if not code:
        raise HTTPException(status_code=400, detail="Bad request")

    state_bytes = base64.b64decode(state)
    state_str = state_bytes.decode("utf-8")
    state_dict = json.loads(state_str)
    # TODO: validate state_dict
    org_id, user_id = state_dict["org_id"], state_dict["user_id"]
    secret_key = format_secret_key(org_id, user_id, provider)
    token_data = exchange_code_for_token(code)
    # store access token in aws secret manager
    # token_data['installation_id'] = installation_id
    secret_value = json.dumps(token_data)
    # secret_value = json.dumps({'token_data': token_data, 'installation_id': installation_id})
    write_secret(secret_key, secret_value)
    value = read_secret(secret_key)
    if value is not None:
        print("Secret stored successfully")

    # If the user is already present in the database, update the installation_id (if, for example, they removed the
    # app and reinstalled it)
    UserRepository(session).create_or_update(user_id, org_id, installation_id)

    content = "<html><body><script>window.close();</script></body></html>"
    return Response(content=content, media_type="text/html")


class GitRepository(BaseModel):
    provider_name: str
    repo_name: str
    org: str
    last_updated: datetime
    metadata: dict


# endpoint to clone repo and pipe to s3
@router.post("/{provider}/clone-repo", dependencies=[ContentEditorPermission])
async def clone_repo(
    session: CurrentSession,
    current_user: UserToken,
    provider: str,
    repo: GitRepository,
):
    secret_key = format_secret_key(
        current_user.organization_id, current_user.user_id, provider
    )
    value = read_secret(secret_key)
    token = None
    workspace_repo = WorkspaceRepository(session)
    default_workspace = workspace_repo.get_default_workspace(
        current_user.organization_id
    )
    if not default_workspace:
        raise HTTPException(status_code=400, detail="Default workspace not found")

    workspace_id = str(default_workspace.id)
    upload_complete = False
    if value is not None:
        s = value["SecretString"]
        secret_sauce = json.loads(s)
        token = secret_sauce["access_token"]
        upload_complete = await download_and_upload_repo(
            repo.org,
            current_user.user_id,
            current_user.organization_id,
            workspace_id,
            repo.repo_name,
            token,
            provider,
        )

    if upload_complete is True:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED, content={"message": "Upload complete"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Upload failed"},
        )


def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if not signature_header:
        raise HTTPException(
            status_code=403, detail="x-hub-signature-256 header is missing!"
        )
    hash_object = hmac.new(
        secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")


@router.post("/{provider}/webhook")
async def webhook(provider: str, request: Request):
    # Ensure the request body is read as bytes for signature verification
    body_bytes = await request.body()  # Get the raw request body as bytes
    body = await request.json()  # Parse the JSON body for further processing
    github_event = request.headers.get("x-github-event", "")
    signature_header = request.headers.get("x-hub-signature-256", "")

    # Verify the GitHub signature
    secret_token = (
        settings.GH_WEBHOOK_SECRET
    )  # Ensure you have this configured in your settings or environment
    try:
        verify_signature(body_bytes, secret_token, signature_header)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    # TODO handle install event
    # TODO handle uninstall event
    # TODO handle revoke event

    # Respond to indicate that the delivery was successfully received
    if github_event == "issues":
        action = body.get("action", "")
        if action == "opened":
            print(f"An issue was opened with this title: {body['issue']['title']}")
        elif action == "closed":
            print(f"An issue was closed by {body['issue']['user']['login']}")
        else:
            print(f"Unhandled action for the issue event: {action}")
    elif github_event == "ping":
        print("GitHub sent the ping event")
    else:
        print(f"Unhandled event: {github_event}")
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"message": "Accepted"}
    )
