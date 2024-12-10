import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime

from database.models_v1 import GithubAppInstallation
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.auth import ContentEditorPermission, UserToken
from app.api.session import CurrentSession
from app.core.config import settings
from app.repositories.workspace_repository import WorkspaceRepository
from app.utils.aws_secrets_manager import format_secret_key, write_secret
from app.utils.gh_ops import (
    download_and_upload_repo,
    exchange_code_for_token,
    fetch_app_access_token,
    verify_app_installation_access,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class OkResponse(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@router.get("/{provider}/callback", response_model=OkResponse)
def git_provider_callback(
    session: CurrentSession,
    provider: str,
    code: str,
    state: str,
    installation_id: str,
    request: Request,
    response: Response,
) -> OkResponse:
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
    secret_value = json.dumps(token_data)
    write_secret(secret_key, secret_value)

    gh_app_install = GithubAppInstallation(
        organization_id=org_id, github_app_installation_id=installation_id
    )
    session.add(gh_app_install)
    session.commit()

    content = "<html><body><script>window.close();</script></body></html>"
    return Response(content=content, media_type="text/html")


class GitRepository(BaseModel):
    provider_name: str
    repo_name: str
    org: str
    last_updated: datetime
    metadata: dict


@router.post("/{provider}/clone-repo", dependencies=[ContentEditorPermission])
def clone_repo(
    session: CurrentSession,
    current_user: UserToken,
    provider: str,
    repo: GitRepository,
) -> JSONResponse:
    if provider != "github":
        raise NotImplementedError()

    workspace_repo = WorkspaceRepository(session)
    default_workspace = workspace_repo.get_default_workspace(
        current_user.organization_id
    )
    if not default_workspace:
        raise HTTPException(status_code=400, detail="Default workspace not found")

    if not verify_app_installation_access(
        session, current_user.organization_id, repo.metadata["installation_id"]
    ):
        logger.error(
            f"User is not authorized to access Github installation id = {repo.metadata["installation_id"]} in organization {current_user.organization_id}"
        )
        raise HTTPException(
            status_code=403, detail="Unauthorized to access this installation ID."
        )

    workspace_id = str(default_workspace.id)
    upload_complete = False

    token = fetch_app_access_token(repo.metadata["installation_id"])
    upload_complete = download_and_upload_repo(
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


def verify_signature(
    payload_body: bytes, secret_token: str, signature_header: str
) -> None:
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


# TODO update this so we kick of the onboarding process on certain events
@router.post("/github/webhook")
async def webhook(request: Request) -> JSONResponse:
    body_bytes = await request.body()
    body = await request.json()
    github_event = request.headers.get("x-github-event", "")
    signature_header = request.headers.get("x-hub-signature-256", "")
    secret_token = settings.GH_WEBHOOK_SECRET

    try:
        verify_signature(body_bytes, secret_token, signature_header)
    except HTTPException as e:
        logger.warning("Signature verification failed")
        return JSONResponse(
            status_code=e.status_code, content={"detail": "Error occurred"}
        )

    if github_event == "push":
        repository = body.get("repository", {})
        org_name = repository.get("owner", {}).get("login", "unknown")
        repo_name = repository.get("name", "unknown")
        default_branch = repository.get("default_branch", "unknown")
        pushed_ref = body.get("ref", "")

        if pushed_ref != f"refs/heads/{default_branch}":
            logger.info(
                "Push event ignored: Not the default branch. Org: %s, Repo: %s, Ref: %s",
                org_name,
                repo_name,
                pushed_ref,
            )
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"message": "Push event ignored (not default branch)"},
            )

        logger.info(
            "Push event on default branch. Org: %s, Repo: %s, Branch: %s",
            org_name,
            repo_name,
            default_branch,
        )
        # TODO: here is where we can check if the last version is complete, and if so,
        #  kick off the onboarding process
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": f"Push event processed for {org_name}/{repo_name}"},
        )

    elif github_event == "ping":
        logger.info("Ping event received from GitHub.")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED, content={"message": "Ping received"}
        )

    logger.info("Unhandled event type: %s", github_event)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"message": "Event ignored"}
    )
