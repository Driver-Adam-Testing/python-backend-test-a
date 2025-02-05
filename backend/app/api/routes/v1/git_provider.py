import base64
import hashlib
import hmac
import json
import logging

import modal
from database.models_v1 import (
    GithubAppInstallation,
    GitProviderApp,
    GitProviderAppInstallation,
)
from database.models_v2 import PrimaryAsset
from database.models_v2_enums import PrimaryAssetKind
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from shared.interfaces.aws_client_config import AWSClientConfig
from sqlmodel import select

from app.api.auth import (
    ContentEditorPermission,
    GitProviderManagerPermission,
    UserToken,
)
from app.api.session import CurrentSession
from app.core.config import settings
from app.repositories.github_app_installations_repository import (
    GithubAppInstallationsRepository,
)
from app.schemas.git_provider_schema import (
    CreateGitProviderAppRequest,
    GitRepository,
)
from app.services.gitlab_provider_service import (
    authorize_git_provider,
    clone_git_repository,
    create_git_provider_app,
    fetch_git_provider_app_install_by_user_id,
    fetch_git_provider_apps_by_org_id,
    fetch_user_repositories_by_app_id,
    handle_authorization_callback,
)
from app.utils.aws_s3 import org_id_to_hash
from app.utils.aws_secrets_manager import format_secret_key, write_secret
from app.utils.gh_ops import (
    download_and_upload_repo,
    exchange_code_for_token,
    fetch_app_access_token,
    verify_app_installation_access,
)

logger = logging.getLogger(__name__)

router = APIRouter()


aws_config = AWSClientConfig(
    region_name="us-east-1",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


class OkResponse(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


#### APP ###
@router.get(
    "/app",
    summary="Get git provider apps",
    response_model=list[GitProviderApp],
)
def get_apps(
    session: CurrentSession,
    current_user: UserToken,
) -> list[GitProviderApp]:
    return fetch_git_provider_apps_by_org_id(session, current_user.organization_id)


@router.post(
    "/app",
    summary="Create git provider app.",
    dependencies=[GitProviderManagerPermission],
    response_model=GitProviderApp,
)
def create_app(
    session: CurrentSession,
    gp_app_input: CreateGitProviderAppRequest,
) -> GitProviderApp:
    return create_git_provider_app(session, gp_app_input, aws_config)


@router.get("/app/{application_id}/authorize")
def get_provider_authorize_url(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
) -> JSONResponse:
    auth_url = authorize_git_provider(
        session,
        current_user.organization_id,
        current_user.user_id,
        application_id,
        aws_config,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"authorize_url": auth_url}
    )


@router.get(
    "/app/{application_id}/installation",
    summary="Get app install for logged in user.",
    response_model=GitProviderAppInstallation,
)
def get_app_installation(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
) -> GitProviderAppInstallation:
    install = fetch_git_provider_app_install_by_user_id(
        session,
        current_user.organization_id,
        current_user.user_id,
        application_id,
    )

    if not install:
        raise HTTPException(status_code=404, detail="Installation not found.")

    return install


@router.get("/app/{application_id}/repos", response_model=list[GitRepository])
def get_user_repositories_by_app_id(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
) -> list[GitRepository]:
    return fetch_user_repositories_by_app_id(
        session,
        current_user.organization_id,
        current_user.user_id,
        application_id,
        aws_config,
    )


@router.get("/app/callback")
def git_provider_app_callback(
    session: CurrentSession,
    state: str,
    code: str | None = None,
    error: str | None = Query(None),
) -> Response:
    if not error and not code:
        raise HTTPException(status_code=400, detail="Bad request")

    if error:  # if the user denies the authorization request
        logger.error(f"Error in callback: {error}")
    else:
        handle_authorization_callback(session, code, state, aws_config)

    content = "<html><body><script>window.close();</script></body></html>"
    return Response(content=content, media_type="text/html")


@router.post("/app/{application_id}/clone-repo", dependencies=[ContentEditorPermission])
def clone_git_provider_repo(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
    repo: GitRepository,
) -> JSONResponse:
    upload_key = (
        f"analysis/{org_id_to_hash(current_user.organization_id)}/{repo.repo_name}.zip"
    )
    bucket_name = (
        settings.DROPZONE_BUCKET_NAME
        if not settings.USE_LEGACY_DROPZONE
        else f"{settings.ENVIRONMENT}-{settings.AWS_S3_CODE_BUCKET_SUFFIX}"
    )
    analysis_download_url = clone_git_repository(
        session,
        current_user.organization_id,
        current_user.user_id,
        application_id,
        repo,
        upload_key,
        bucket_name,
        aws_config,
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"download_url": analysis_download_url},
    )


### GIT PROVIDER ###


@router.get("/github/callback", response_model=OkResponse)
def github_callback(
    session: CurrentSession,
    code: str,
    state: str,
    installation_id: str,
    request: Request,
    response: Response,
) -> OkResponse:
    if not code:
        raise HTTPException(status_code=400, detail="Bad request")

    state_bytes = base64.b64decode(state)
    state_str = state_bytes.decode("utf-8")
    state_dict = json.loads(state_str)
    # TODO: validate state_dict
    org_id, user_id = state_dict["org_id"], state_dict["user_id"]
    secret_key = format_secret_key(org_id, user_id, "github")
    token_data = exchange_code_for_token(code)
    secret_value = json.dumps(token_data)
    write_secret(secret_key, secret_value)

    existing_installation = session.exec(
        select(GithubAppInstallation).where(
            GithubAppInstallation.organization_id == org_id,
            GithubAppInstallation.github_app_installation_id == installation_id,
        )
    ).first()

    if existing_installation is None:
        logging.info(
            f"Creating github app installation for org = {org_id}, installation = {installation_id}"
        )
        gh_app_install = GithubAppInstallation(
            organization_id=org_id, github_app_installation_id=installation_id
        )
        session.add(gh_app_install)
        session.commit()

    # handle_github_events = modal.Function.lookup("inspector_v2", "handle_github_events")
    # handle_github_events.spawn(installation_id, org_id)

    content = "<html><body><script>window.close();</script></body></html>"
    return Response(content=content, media_type="text/html")


@router.post("/{provider}/clone-repo", dependencies=[ContentEditorPermission])
def clone_repo(
    session: CurrentSession,
    current_user: UserToken,
    provider: str,
    repo: GitRepository,
) -> JSONResponse:
    if provider != "github":
        raise NotImplementedError()

    if not verify_app_installation_access(
        session, current_user.organization_id, repo.metadata["installation_id"]
    ):
        logger.error(
            f"User is not authorized to access Github installation id = {repo.metadata["installation_id"]} "
            f"in organization {current_user.organization_id}"
        )
        raise HTTPException(
            status_code=403, detail="Unauthorized to access this installation ID."
        )

    token = fetch_app_access_token(repo.metadata["installation_id"])
    upload_key = (
        f"analysis/{org_id_to_hash(current_user.organization_id)}/{repo.repo_name}.zip"
    )
    upload_complete, analysis_download_url = download_and_upload_repo(
        gh_org_name=repo.org,
        owner=current_user.user_id,
        org_id=current_user.organization_id,
        repo=repo.repo_name,
        repo_id=str(repo.metadata["id"]),
        access_token=token,
        upload_key=upload_key,
    )

    if upload_complete is True:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"download_url": analysis_download_url},
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


def handle_installation_create_event(
    session: CurrentSession, body: dict
) -> JSONResponse:
    installation_id = str(body["installation"]["id"])
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

    repositories = body["repositories"]
    repos_added = []
    repos_deleted = []
    repos_pushed = []
    for repo in repositories:
        repos_added.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
            }
        )

    handle_github_events = modal.Function.lookup("inspector_v2", "handle_github_events")
    handle_github_events.spawn(
        installation_id,
        gh_app_install.organization_id,
        repos_added,
        repos_deleted,
        repos_pushed,
    )

    logger.info(
        f"Installation create event processed for {installation_id}. Connecting repos."
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": ""},
    )


def handle_installation_delete_event(
    session: CurrentSession, body: dict
) -> JSONResponse:
    installation_id = str(body["installation"]["id"])
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

    repositories = body["repositories"]
    repos_added = []
    repos_deleted = []
    repos_pushed = []
    for repo in repositories:
        repos_deleted.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
            }
        )

    handle_github_events = modal.Function.lookup("inspector_v2", "handle_github_events")
    handle_github_events.spawn(
        installation_id,
        gh_app_install.organization_id,
        repos_added,
        repos_deleted,
        repos_pushed,
    )

    logger.info(
        f"Installation delete event processed for {installation_id}. Disconnecting repos."
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": ""},
    )


def handle_installation_modified_event(
    session: CurrentSession, body: dict
) -> JSONResponse:
    installation_id = str(body["installation"]["id"])
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

    body_repos_added = body["repositories_added"]
    body_repos_removed = body["repositories_removed"]

    repos_added = []
    repos_deleted = []
    repos_pushed = []

    for repo in body_repos_added:
        # This repo may already be connected, okay to have integrityerror in modal?
        repos_added.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
            }
        )

    for repo in body_repos_removed:
        repos_deleted.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
            }
        )

    handle_github_events = modal.Function.lookup("inspector_v2", "handle_github_events")
    handle_github_events.spawn(
        installation_id,
        gh_app_install.organization_id,
        repos_added,
        repos_deleted,
        repos_pushed,
    )

    logger.info(
        f"Installation modified event processed for {installation_id}. Connecting repos."
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": ""},
    )


def handle_push_event(session: CurrentSession, body: dict) -> JSONResponse:
    repository = body["repository"]
    org_name = repository.get("owner", {}).get("login", "unknown")
    repo_name = repository["name"]
    repo_id = str(repository["id"])
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

    codebase_asset = get_codebase_asset(
        session, gh_app_install.organization_id, repo_name
    )
    if not codebase_asset:
        logger.warning(
            "Codebase primary asset record not found for repo: %s", repo_name
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": ""},
        )

    repos_added = []
    repos_deleted = []
    repos_pushed = [
        {
            "id": repo_id,
            "name": repo_name,
            "full_name": repository["full_name"],
            "commit": commit_hash,
        }
    ]
    handle_github_events = modal.Function.lookup("inspector_v2", "handle_github_events")
    handle_github_events.spawn(
        installation_id,
        gh_app_install.organization_id,
        repos_added,
        repos_deleted,
        repos_pushed,
    )

    logger.info(
        f"Push event processed for repo: {repo_name}. Processing in background job."
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": ""},
    )

    # upload_key = (
    #     f"codebases/{org_id_to_hash(gh_app_install.organization_id)}/{repo_name}.zip"
    # )
    # token = fetch_app_access_token(installation_id)
    # upload_complete, _ = download_and_upload_repo(
    #     gh_org_name=org_name,
    #     owner="",
    #     org_id=gh_app_install.organization_id,
    #     repo=repo_name,
    #     repo_id=repo_id,
    #     access_token=token,
    #     commit=commit_hash,
    #     upload_key=upload_key,
    # )

    # if upload_complete:
    #     logger.info("Repository push event successfully processed: %s", repo_name)
    #     return JSONResponse(
    #         status_code=status.HTTP_202_ACCEPTED,
    #         content={"message": ""},
    #     )
    # else:
    #     logger.error("Repository upload failed in webhook: %s", repo_name)
    #     return JSONResponse(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": ""}
    #     )


def get_codebase_asset(
    session: CurrentSession, org_id: str, repo_name: str
) -> PrimaryAsset:
    primary_asset = session.exec(
        select(PrimaryAsset).where(
            PrimaryAsset.organization_id == org_id,
            PrimaryAsset.display_name == repo_name,
            PrimaryAsset.kind == PrimaryAssetKind.CODEBASE,
        )
    ).one_or_none()
    return primary_asset


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

    # TODO: create github payload to pass into handle_github_events modal function.
    # Need: GH org, repo_id, repo name

    if github_event == "push":
        return handle_push_event(session, body)
    elif github_event == "ping":
        return handle_ping_event()
    elif github_event == "installation":
        if body["action"] == "created":
            return handle_installation_create_event(session, body)
        elif body["action"] == "deleted":
            installation_record = session.exec(
                select(GithubAppInstallation).where(
                    GithubAppInstallation.github_app_installation_id
                    == str(body["installation"]["id"])
                )
            ).first()
            session.delete(installation_record)
            session.commit()
            return handle_installation_delete_event(session, body)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED, content={"message": ""}
        )
    elif github_event == "installation_repositories":
        # Add or remove event. An edit causes two github events
        return handle_installation_modified_event(session, body)

    logger.info("Unhandled event type: %s", github_event)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"message": "Event ignored"}
    )
