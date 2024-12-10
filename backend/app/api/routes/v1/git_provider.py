import base64
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime

from database.models_v1 import DerivedContent, DerivedContentType, GithubAppInstallation
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import select

from app.api.auth import ContentEditorPermission, UserToken
from app.api.session import CurrentSession
from app.core.config import settings
from app.repositories.github_app_installations_repository import (
    GithubAppInstallationsRepository,
)
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


async def _extract_body_and_headers(request: Request) -> dict:
    body_bytes = await request.body()
    body_json = json.loads(body_bytes)
    return {"raw_body": body_bytes, "json_body": body_json, "headers": request.headers}


def verify_github_signature(
    body_bytes: bytes, secret_token: str, signature_header: str
) -> None:
    try:
        verify_signature(body_bytes, secret_token, signature_header)
    except HTTPException as e:
        logger.warning("Signature verification failed")
        raise e


def handle_push_event(session: CurrentSession, body: dict) -> JSONResponse:
    repository = body["repository"]
    org_name = repository.get("owner", {}).get("login", "unknown")
    repo_name = repository["name"]
    default_branch = repository["default_branch"]
    pushed_ref = body["ref"]
    installation_id = str(body["installation"]["id"])
    commit_hash = body["after"]

    if pushed_ref != f"refs/heads/{default_branch}":
        logger.info(
            "Push event ignored: Not the default branch. Org: %s, Repo: %s, Ref: %s, Install ID: %s",
            org_name,
            repo_name,
            pushed_ref,
            installation_id,
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": "Push event ignored (not default branch)"},
        )

    logger.info(
        "Push event on default branch. Org: %s, Repo: %s, Branch: %s, Install ID: %s",
        org_name,
        repo_name,
        default_branch,
        installation_id,
    )

    # We assume the installation ID is only into one org...
    gh_app_install = GithubAppInstallationsRepository(session).list_by_installation_id(
        installation_id
    )[0]

    if not gh_app_install:
        logger.warning(
            "Installation ID not found in the database; need a row for this app install"
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED, content={"message": ""}
        )

    default_workspace = WorkspaceRepository(session).get_default_workspace(
        gh_app_install.organization_id
    )

    codebase_content_record = get_codebase_content_record(
        session, default_workspace.id, repo_name
    )
    if not codebase_content_record:
        logger.warning("Codebase content record not found for repo: %s", repo_name)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": ""},
        )

    token = fetch_app_access_token(installation_id)
    upload_complete = download_and_upload_repo(
        gh_org_name=org_name,
        owner="",
        org_id=gh_app_install.organization_id,
        workspace_id=str(default_workspace.id),
        repo=repo_name,
        access_token=token,
        commit=commit_hash,
    )

    if upload_complete:
        logger.info("Repository push event successfully processed: %s", repo_name)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": ""},
        )
    else:
        logger.error("Repository upload failed in webhook: %s", repo_name)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": ""}
        )


def get_codebase_content_record(
    session: CurrentSession, default_workspace: uuid.UUID, repo_name: str
) -> DerivedContent:
    statement = (
        select(DerivedContent)
        .join(
            DerivedContentType,
            DerivedContent.content_type_id == DerivedContentType.id,
        )
        .where(
            DerivedContentType.type_name == "codebase",
            DerivedContent.workspace_id == default_workspace,
            DerivedContent.relative_path == repo_name,
        )
    )
    return session.exec(statement).one_or_none()


def handle_ping_event() -> JSONResponse:
    logger.info("Ping event received from GitHub.")
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"message": "Ping received"}
    )


@router.post("/github/webhook")
def webhook(
    session: CurrentSession, body_data: dict = Depends(_extract_body_and_headers)
) -> JSONResponse:
    body_bytes = body_data["raw_body"]
    body = body_data["json_body"]
    headers = body_data["headers"]

    github_event = headers.get("x-github-event", "")
    signature_header = headers.get("x-hub-signature-256", "")

    secret_token = settings.GH_WEBHOOK_SECRET

    verify_github_signature(body_bytes, secret_token, signature_header)

    if github_event == "push":
        return handle_push_event(session, body)
    elif github_event == "ping":
        return handle_ping_event()
    elif github_event == "installation":
        if body["action"] == "deleted":
            installation_record = session.exec(
                select(GithubAppInstallation).where(
                    GithubAppInstallation.github_app_installation_id
                    == str(body["installation"]["id"])
                )
            ).first()
            session.delete(installation_record)
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED, content={"message": ""}
        )

    logger.info("Unhandled event type: %s", github_event)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"message": "Event ignored"}
    )
