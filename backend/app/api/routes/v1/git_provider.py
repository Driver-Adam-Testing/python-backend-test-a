import base64
import hashlib
import hmac
import json
import logging
from itertools import groupby
from uuid import UUID

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
    OrgManagerPermission,
    UserToken,
)
from app.api.session import CurrentSession
from app.core.config import settings
from app.git_providers.utils.errors import (
    GitProviderAccessTokenError,
)
from app.repositories.git_provider_repository import (
    git_provider_app_installation_by_id,
    git_provider_app_installation_by_org_id,
)
from app.repositories.github_app_installations_repository import (
    GithubAppInstallationsRepository,
)
from app.schemas.git_provider_schema import (
    CreateGitProviderAppRequest,
    GitRepository,
    GroupAccessToken,
)
from app.services.gitlab_provider_service import (
    authorize_git_provider,
    clone_git_repository,
    create_git_provider_app,
    fetch_git_provider_apps_by_org_id,
    fetch_group_repositories_by_app_id,
    handle_authorization_callback,
    handle_delete_git_provider_app,
    handle_group_access_revoke,
    install_group_access_token,
)
from app.utils.aws_s3 import org_id_to_hash
from app.utils.aws_secrets_manager import format_secret_key, write_secret
from app.utils.gh_ops import (
    download_and_upload_repo,
    exchange_code_for_token,
    fetch_app_access_token,
    fetch_commit_hash,
    verify_app_installation_access,
)

logger = logging.getLogger(__name__)

router = APIRouter()

NO_OS_DRIVER_BRANCH = "staging/docs"
NO_OS_REPO_NAME = "no-OS"
NO_OS_GH_ORG = "analogdevicesinc"

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
    dependencies=[OrgManagerPermission],
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
    dependencies=[OrgManagerPermission],
    response_model=GitProviderApp,
)
def create_app(
    session: CurrentSession,
    gp_app_input: CreateGitProviderAppRequest,
) -> GitProviderApp:
    return create_git_provider_app(session, gp_app_input, aws_config)


@router.delete(
    "/app/{application_id}",
    summary="Delete git provider app.",
    dependencies=[OrgManagerPermission],
)
def delete_git_provider_app(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
) -> JSONResponse:
    handle_delete_git_provider_app(
        session, current_user.organization_id, application_id, aws_config
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "App deleted."},
    )


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
    "/app/{application_id}/installations",
    summary="Get app install for logged.",
    response_model=list[GitProviderAppInstallation],
    dependencies=[OrgManagerPermission],
)
def get_app_installation(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
) -> list[GitProviderAppInstallation]:
    installs = git_provider_app_installation_by_org_id(
        session,
        current_user.organization_id,
        application_id,
    )
    return installs


@router.post(
    "/app/{application_id}/token",
    summary="Add a group access token to the app.",
    dependencies=[OrgManagerPermission],
)
def add_group_access_token(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
    gat: GroupAccessToken,
) -> JSONResponse:
    try:
        install = install_group_access_token(
            session, current_user.organization_id, application_id, gat, aws_config
        )

        if not install:
            raise HTTPException(status_code=404, detail="Installation not found.")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Token added."},
        )
    except GitProviderAccessTokenError:
        logger.exception("Error adding token")
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.delete(
    "/app/{application_id}/installations/{installation_id}",
    dependencies=[OrgManagerPermission],
    summary="Delete app install",
)
def delete_app_installation(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
    installation_id: str,
) -> JSONResponse:
    handle_group_access_revoke(
        session,
        current_user.organization_id,
        application_id,
        installation_id,
        aws_config,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Installation deleted."},
    )


@router.get(
    "/app/{application_id}/repos",
    dependencies=[OrgManagerPermission],
    response_model=list[GitRepository],
)
def get_user_repositories_by_app_id(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
) -> list[GitRepository]:
    try:
        return fetch_group_repositories_by_app_id(
            session,
            current_user.organization_id,
            current_user.user_id,
            application_id,
            aws_config,
        )
    except GitProviderAccessTokenError as e:
        logger.error(f"Error fetching repositories: {e}")
        # give me a 403 if the user is not authorized to access the installation
        raise HTTPException(status_code=403, detail="Insufficient permissions")


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


@router.post(
    "/app/{application_id}/connect-repos",
    dependencies=[OrgManagerPermission],
)
def connect_git_provider_repo(
    session: CurrentSession,
    current_user: UserToken,
    application_id: str,
    repos: list[GitRepository],
) -> JSONResponse:
    handle_gitlab_events = modal.Function.lookup(
        "inspector-v2",
        "handle_gitlab_events",
        environment_name=settings.MODAL_ENVIRONMENT,
    )

    repos.sort(key=lambda x: x.installation_id)
    installation_groups = {
        k: list(v) for k, v in groupby(repos, key=lambda x: x.installation_id)
    }
    for installation_id, repo_group in installation_groups.items():
        app_install = git_provider_app_installation_by_id(session, installation_id)
        if (
            app_install.git_provider_app_id != application_id
            or app_install.organization_id != current_user.organization_id
        ):
            raise HTTPException(status_code=404, detail="Installation not found.")
        handle_gitlab_events.spawn(
            installation_id,
            current_user.organization_id,
            repos_added=[repo.model_dump() for repo in repo_group],
            repos_deleted=[],
            repos_pushed=[],
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": "Connecting"},
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
    write_secret(
        secret_key, secret_value
    )  # TODO make sure these are unused and stop saving them to avoid confusion.

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

        connect_repos = modal.Function.lookup(
            "inspector-v2", "connect_repos_for_installation"
        )
        connect_repos.spawn(installation_id)

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

    # Defer to default branch if not the driver branch of no-OS for ADI
    # TODO this is an ADI-specific hack!
    if repo.repo_name == NO_OS_REPO_NAME and repo.org == NO_OS_GH_ORG:
        commit_sha = fetch_commit_hash(
            NO_OS_GH_ORG, NO_OS_REPO_NAME, NO_OS_DRIVER_BRANCH, token
        )
    elif repo.repo_name == "diff-tests" and repo.org == "driver-ai":
        commit_sha = fetch_commit_hash("driver-ai", "diff-tests", "adi_test", token)
    else:
        commit_sha = None

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
        commit=commit_sha,
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


def handle_installation_delete_event(
    session: CurrentSession, body: dict
) -> JSONResponse:
    installation_id = str(body["installation"]["id"])
    installation_record = session.exec(
        select(GithubAppInstallation).where(
            GithubAppInstallation.github_app_installation_id == installation_id
        )
    ).first()
    org_id = installation_record.organization_id
    session.delete(installation_record)
    session.commit()
    installation_id = None

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

    handle_github_events = modal.Function.lookup("inspector-v2", "handle_github_events")
    handle_github_events.spawn(
        installation_id,
        org_id,
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

    handle_github_events = modal.Function.lookup("inspector-v2", "handle_github_events")
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

    if org_name == NO_OS_GH_ORG and repo_name == NO_OS_REPO_NAME:
        if pushed_ref != f"refs/heads/{NO_OS_DRIVER_BRANCH}":
            logger.info(
                "ADI event ignored: Not the driver branch of no-OS. Org: %s, Repo: %s, Ref: %s, Install ID: %s",
                org_name,
                repo_name,
                pushed_ref,
                installation_id,
            )
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"message": "Push event ignored (not driver branch)"},
            )
    elif org_name == "driver-ai" and repo_name == "diff-tests":
        if pushed_ref != "refs/heads/adi_test":
            logger.info(
                "ADI event ignored: Not the adi_test branch of diff-tests. Org: %s, Repo: %s, Ref: %s, Install ID: %s",
                org_name,
                repo_name,
                pushed_ref,
                installation_id,
            )
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"message": "Push event ignored (not adi_test branch)"},
            )
    elif pushed_ref != f"refs/heads/{default_branch}":
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
    handle_github_events = modal.Function.lookup("inspector-v2", "handle_github_events")
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

    if github_event == "push":
        return handle_push_event(session, body)
    elif github_event == "ping":
        return handle_ping_event()
    elif github_event == "installation":
        # TODO handle installation suspension;
        if body["action"] == "deleted":
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


def handle_gitlab_push_event(
    session: CurrentSession,
    app_id: UUID,
    installation_id: str,
    body: dict,
) -> JSONResponse:
    repository = body["repository"]
    project = body["project"]
    repo_name = repository["name"]
    repo_id = str(project["id"])
    full_name = project["path_with_namespace"]
    default_branch = project["default_branch"]
    pushed_ref = body["ref"]
    commit_hash = body["after"]
    app_install = git_provider_app_installation_by_id(session, installation_id)
    organization_id = app_install.organization_id

    if pushed_ref != f"refs/heads/{default_branch}":
        logger.info(
            "Push event ignored: Not the default branch. Org: %s, Repo: %s, Ref: %s, Install ID: %s",
            organization_id,
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
        organization_id,
        repo_name,
        default_branch,
        installation_id,
    )

    if app_install.git_provider_app_id != app_id:
        raise HTTPException(status_code=404, detail="Installation not found.")

    repos_pushed = [
        {
            "id": repo_id,
            "name": repo_name,
            "repo_name": repo_name,
            "full_name": full_name,
            "commit": commit_hash,
            "metadata": project,
            "installation_id": installation_id,
            "latest_commit": {
                "commit": {
                    "id": commit_hash,
                },
            },
        }
    ]
    handle_github_events = modal.Function.lookup(
        "inspector-v2",
        "handle_gitlab_events",
        environment_name=settings.MODAL_ENVIRONMENT,
    )
    handle_github_events.spawn(
        installation_id,
        organization_id,
        [],
        [],
        repos_pushed,
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"ok": ""},
    )


@router.post("/app/webhook")
def gitlab_webhook(
    session: CurrentSession,
    body_data: dict = Depends(_extract_body_and_headers),
) -> JSONResponse:
    # TODO: Use install id as the token
    # TODO: handle token expire events
    body = body_data["json_body"]
    headers = body_data["headers"]
    object_kind = body.get("object_kind")
    installation_id = headers["x-gitlab-token"]
    app_install = git_provider_app_installation_by_id(session, installation_id)

    if object_kind == "push":
        print("Push event")
        handle_gitlab_push_event(
            session, app_install.git_provider_app_id, installation_id, body
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"message": "Event ignored"}
    )
