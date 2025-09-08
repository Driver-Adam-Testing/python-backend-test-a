import base64
import hashlib
import logging
import os
import re
import time
from uuid import UUID

import httpx
import jwt
import requests
from database.models import VcsAutoUpdatePolicy
from onboarding.onboard_utils import AccessTokenError
from onboarding.vcs_utils import (
    AuthorInfo,
    BranchInfo,
    CommitInfo,
    RepoInfo,
    VersionControlInfo,
)
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


def generate_jwt() -> str:
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "iss": os.environ["GH_CLIENT_ID"],
    }
    decoded_pem = base64.b64decode(os.environ["GH_CLIENT_PEM_SECRET"])
    return jwt.encode(payload, decoded_pem, algorithm="RS256")


def fetch_app_access_token(installation_id: str) -> str:
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    jwt = generate_jwt()
    with httpx.Client() as client:
        headers = {"Accept": "application/json", "Authorization": f"Bearer {jwt}"}
        response = client.post(url, headers=headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise AccessTokenError(
                    f"GitHub application installation {installation_id} not found."
                ) from e
            raise
        token_data = response.json()
        if "token" not in token_data:
            raise AccessTokenError("GitHub application access token not found.")
        return token_data["token"]


# modal run --env=dev-ericmiller


def get_github_repo_url(full_repo_name: str) -> str:
    return f"https://api.github.com/repos/{full_repo_name}"


def fetch_default_branch_and_commit(full_repo_name: str, access_token: str) -> str:
    headers = {"Authorization": f"token {access_token}"}
    repo_url = get_github_repo_url(full_repo_name=full_repo_name)

    repo = requests.get(repo_url, headers=headers)
    repo_data = repo.json()
    logger.info(
        f"Repo information retrieved from github API (status code {repo.status_code}): {repo_data}"
    )
    default_branch = repo_data["default_branch"]

    branch_url = f"{repo_url}/branches/{default_branch}"
    branch_response = requests.get(branch_url, headers=headers)
    branch_data = branch_response.json()
    logger.info(f"Default branch for {full_repo_name} is {default_branch}")
    logger.info(
        f"Branch data retrieved from github API (status code {branch_response.status_code}): {branch_data}"
    )
    return branch_data["commit"]["sha"]


def fetch_vcs_info(
    full_repo_name: str, access_token: str, commit_sha: str
) -> VersionControlInfo:
    headers = {"Authorization": f"token {access_token}"}
    repo_url = get_github_repo_url(full_repo_name=full_repo_name)

    repo = requests.get(repo_url, headers=headers)
    repo_data = repo.json()
    logger.info(
        f"Repo information retrieved from github API (status code {repo.status_code}): {repo_data}"
    )
    default_branch = repo_data["default_branch"]

    commit_url = f"{repo_url}/commits/{commit_sha}"
    commit_response = requests.get(commit_url, headers=headers)
    commit_data = commit_response.json()
    logger.info(
        f"Commit data retrieved from github API (status code {commit_response.status_code}): {commit_data}"
    )
    author_info = AuthorInfo(
        email=commit_data["commit"]["author"]["email"],
        name=commit_data["commit"]["author"]["name"],
        date=commit_data["commit"]["author"]["date"],
    )
    commit_info = CommitInfo(
        sha=commit_data["sha"],
        message=commit_data["commit"]["message"],
        url=commit_data["html_url"],
        author=author_info,
    )
    branch_info = BranchInfo(name=default_branch)
    repo_info = RepoInfo(
        name=repo_data["name"],
        namespace=repo_data["owner"]["login"],
        full_name=repo_data["full_name"],
        url=repo_data["html_url"],
    )
    return VersionControlInfo(
        repository=repo_info,
        commit=commit_info,
        branch=branch_info,
    )


def fetch_github_default_branch_name(full_repo_name: str, access_token: str) -> str:
    headers = {"Authorization": f"token {access_token}"}
    repo_url = get_github_repo_url(full_repo_name=full_repo_name)
    repo = requests.get(repo_url, headers=headers)
    repo_data = repo.json()
    return repo_data["default_branch"]


def generate_codebase_metadata(
    org_id: str,
    full_repo_name: str,
    repo_id: str | int,
    provider: str,
    version_id: str | UUID,
    asset_name: str,
    install_id: str,
) -> dict:
    from database.models_enums import PrimaryAssetKind

    return {
        "unhashed_organization_id": org_id,
        "full_repo_name": full_repo_name,  # NOTE: just used for debugging
        "provider": provider,
        "version_id": str(version_id),
        "repository_id": str(repo_id),  # NOTE: just used for debugging
        "asset_name": asset_name,
        "asset_kind": PrimaryAssetKind.CODEBASE,
        "install_id": install_id,
    }


def download_github_repo_zip(full_name: str, commit: str, access_token: str) -> bytes:
    headers = {"Authorization": f"token {access_token}"}
    zip_url = f"https://api.github.com/repos/{full_name}/zipball/{commit}"
    response = requests.get(zip_url, headers=headers, timeout=120, allow_redirects=True)
    response.raise_for_status()
    return response.content


def download_and_upload_repo(
    org_id: str,
    repo: dict,
    access_token: str,
    install_id: str,
    is_push: bool = False,
) -> str | None:
    from database.db import engine
    from database.models import PrimaryAsset, Version
    from database.models_enums import (
        PrimaryAssetKind,
        PrimaryAssetProvider,
        VersionStatus,
    )
    from onboarding.onboard_utils import upload_to_s3_with_metadata
    from sqlalchemy.exc import IntegrityError

    if not repo.get("commit"):
        try:
            commit = fetch_default_branch_and_commit(repo["full_name"], access_token)
        except KeyError:
            print(f"Failed to find commit for {repo}, unable to process")
            return repo
    else:
        commit = repo["commit"]
    try:
        vcs_info = fetch_vcs_info(
            full_repo_name=repo["full_name"],
            access_token=access_token,
            commit_sha=commit,
        )
        with Session(engine) as session, session.begin():
            if is_push:
                primary_asset = session.exec(
                    select(PrimaryAsset)
                    .where(
                        PrimaryAsset.organization_id == org_id,
                        PrimaryAsset.repository_id == repo["id"],
                    )
                    .options(selectinload(PrimaryAsset.versions))
                ).first()
                if not primary_asset:
                    print(
                        f"Failed to find primary asset for {repo} for org: {org_id}, unable to process push event, unable to process push event"
                    )
                    return repo
                primary_asset_id = primary_asset.id
                if all(
                    v.status == VersionStatus.CONNECTED for v in primary_asset.versions
                ):
                    new_version = Version(
                        primary_asset_id=primary_asset.id,
                        vcs_hash=commit,
                        status=VersionStatus.CONNECTING,
                        previous_version_id=primary_asset.versions[
                            0
                        ].id,  # TODO: don't link this for connected only?
                        vcs_metadata=vcs_info.model_dump(),
                    )
                    session.add(new_version)
                    version_id = new_version.id
                elif any(
                    v.status
                    in [
                        VersionStatus.GENERATING,
                        VersionStatus.GENERATION_COMPLETE,
                        VersionStatus.GENERATION_ERROR,
                    ]
                    for v in primary_asset.versions
                ):
                    # versions are in descending order of creation
                    for version in primary_asset.versions:
                        if version.status in [
                            VersionStatus.GENERATION_COMPLETE,
                            VersionStatus.GENERATION_ERROR,
                        ]:
                            new_version = Version(
                                primary_asset_id=primary_asset.id,
                                vcs_hash=commit,
                                status=VersionStatus.GENERATING,  # Immediately jump to generating. This signals run_codebase_connection to start inspection after connection
                                previous_version_id=version.id,
                                vcs_metadata=vcs_info.model_dump(),
                            )
                            session.add(new_version)
                            version_id = new_version.id
                            break
                        elif version.status == VersionStatus.GENERATING:
                            # STOPGAP: Ignore push events during active generation to ensure completion
                            print(
                                f"Generation already in progress for {repo.get('name', 'unknown')}. "
                                f"Ignoring push event to allow current generation to complete."
                            )
                            return repo
                            # # Delete running version, and restart inspection with the new version,
                            # # this way the docs we generate reflect the most up to date state
                            # run_statement = (
                            #     select(InspectorRun)
                            #     .where(InspectorRun.version_id == version.id)
                            #     .order_by(InspectorRun.created_at.desc())
                            # )
                            # run = session.exec(run_statement).first()
                            #
                            # if run is not None:
                            #     call_id = run.call_id
                            #     modal_call = modal.FunctionCall.from_id(call_id)
                            #     modal_call.cancel()
                            # # else: the run possibly hasn't been created yet, we'll proceed with the version deletion
                            # session.delete(version)
                            # # Find and delete the usage session for the version
                            # print("Fetching existing usage session...")
                            # usage_session_statement = (
                            #     select(UsageSession)
                            #     .join(
                            #         UsageEvent, UsageSession.id == UsageEvent.session_id
                            #     )
                            #     .where(
                            #         UsageSession.session_metadata["version_id"].astext
                            #         == str(version.id)
                            #     )
                            #     .where(
                            #         UsageEvent.event_type
                            #         == UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT
                            #     )
                            #     .options(selectinload(UsageSession.usage_events))
                            # )
                            # usage_session = session.exec(
                            #     usage_session_statement
                            # ).first()
                            # print(usage_session)
                            # if usage_session is not None:
                            #     usage_event = next(
                            #         (
                            #             event
                            #             for event in usage_session.usage_events
                            #             if event.event_type
                            #             == UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT.value
                            #         ),
                            #         None,
                            #     )
                            #     print(
                            #         f"Found {len(usage_session.usage_events)} usage events for version {version.id}"
                            #     )
                            #     if usage_event is not None:
                            #         new_usage_session = UsageSession(
                            #             status=usage_session.status,
                            #             organization_id=usage_session.organization_id,
                            #             user_id="SYSTEM",
                            #             session_metadata=usage_session.session_metadata,
                            #         )
                            #         session.add(new_usage_session)
                            #         usage_event_credit = UsageEvent(
                            #             **usage_event.dict(
                            #                 exclude={
                            #                     "id",
                            #                     "bytes_in",
                            #                     "session_id",
                            #                     "timestamp",
                            #                     "event_type",
                            #                 }
                            #             ),
                            #             event_type=UsageEventType.ADDITIONAL_PLATFORM_USAGE_CREDIT,
                            #             session_id=new_usage_session.id,
                            #             bytes_in=abs(usage_event.bytes_in),
                            #             timestamp=datetime.now(tz=UTC),
                            #         )
                            #         print(usage_event_credit)
                            #         print(
                            #             f"crediting {usage_event_credit.bytes_in} bytes back to version {version.id}"
                            #         )
                            #         session.add(usage_event_credit)
                            #
                            # new_version = Version(
                            #     primary_asset_id=primary_asset.id,
                            #     vcs_hash=commit,
                            #     status=VersionStatus.GENERATING,  # Immediately jump to generating. This signals run_codebase_connection to start inspection after connection
                            #     previous_version_id=version.previous_version_id,
                            #     vcs_metadata=vcs_info.model_dump(),
                            # )
                            # session.add(new_version)
                            # version_id = new_version.id
                            #
                            # print(
                            #     f"Version already in generating state for {repo["name"]}, deleting existing version and restarting inspection with new version..."
                            # )
                            # break
                elif primary_asset.versions[0].status == VersionStatus.CONNECTING:
                    print(
                        f"Version already in connecting state for {repo["name"]}, skipping..."
                    )
                    return repo
                else:
                    # TODO: any other cases to handle explicitly?
                    return repo

            else:
                primary_asset = PrimaryAsset(
                    display_name=repo["name"],
                    organization_id=org_id,
                    kind=PrimaryAssetKind.CODEBASE,
                    repository_id=repo["id"],
                    codebase_settings_auto_commit_docs=False,
                    provider=PrimaryAssetProvider.GITHUB,
                    vcs_auto_update_policy=VcsAutoUpdatePolicy.AFTER_EVERY_COMMIT,
                )
                session.add(primary_asset)
                primary_asset_id = primary_asset.id

                version = Version(
                    primary_asset_id=primary_asset.id,
                    vcs_hash=commit,
                    status=VersionStatus.CONNECTING,
                    previous_version_id=None,
                    vcs_metadata=vcs_info.model_dump(),
                )
                session.add(version)
                version_id = version.id
                print(
                    f"Creating primary asset and version for {repo["name"]}:{commit} for org: {org_id}. Version ID: {version_id}"
                )
    except IntegrityError:
        print(
            f"Failed to create primary asset and version {repo["name"]}:{commit} for org: {org_id}"
        )
        return repo

    # TODO: update this metadata for latest updates to onboarding logic
    metadata = generate_codebase_metadata(
        org_id,
        repo["full_name"],
        repo["id"],
        "github",
        version_id,
        repo["name"],
        install_id,
    )

    zip_content = download_github_repo_zip(repo["full_name"], commit, access_token)
    logger.info("Repository downloaded successfully. Size: %d bytes", len(zip_content))

    org_hashed_id = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    # TODO: make a helper for constructing the upload key
    upload_key = (
        f"assets/{org_hashed_id}/{primary_asset_id}/{version_id}/{repo['name']}.zip"
    )
    upload_to_s3_with_metadata(zip_content, metadata, upload_key)
    print(f"Repository {repo['name']} uploaded successfully to {upload_key}.")

    return None


def get_repo_clone_info_from_id(repo_id: str, github_token: str) -> tuple[str, str]:
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }

    with httpx.Client() as client:
        resp = client.get(
            f"https://api.github.com/repositories/{repo_id}", headers=headers
        )
        resp.raise_for_status()
        data = resp.json()

    full_name = data["full_name"]  # e.g., "org/repo"
    clone_url = f"https://x-access-token:{github_token}@github.com/{full_name}.git"
    return clone_url, full_name


def list_pull_requests(full_name: str, access_token: str) -> list:
    # Default behavior of Github API fetches only open PRs
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    all_prs = []
    page_count = 1
    with httpx.Client() as client:
        url = f"https://api.github.com/repos/{full_name}/pulls"
        response = client.get(
            url,
            headers=headers,
        )
        response.raise_for_status()
        all_prs.extend(response.json())

        # handle pagination
        link_header = response.headers.get("link", None)
        while link_header is not None:
            page_count = page_count + 1
            parts = response.headers["link"].split(",")
            matches = [
                re.search(r'<([^>]+)>; rel="([^"]+)"', part.strip()) for part in parts
            ]
            has_next = False
            for match in matches:
                next_url, rel = match.groups()
                if rel == "next" and next_url:
                    has_next = True
                    response = client.get(next_url, headers=headers)
                    response.raise_for_status()
                    all_prs.extend(response.json())
            if not has_next:
                break
    return all_prs


def get_pull_request_commits(full_name: str, pr_id: int, access_token: str) -> list:
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    with httpx.Client() as client:
        url = f"https://api.github.com/repos/{full_name}/pulls/{pr_id}/commits"
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def close_pull_request(full_name: str, pr_id: int, access_token: str) -> None:
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    with httpx.Client() as client:
        url = f"https://api.github.com/repos/{full_name}/pulls/{pr_id}"
        response = client.patch(url, headers=headers, json={"state": "closed"})
        response.raise_for_status()
        print(f"✅ Closed pull request {pr_id} for {full_name}")


def create_pull_request_with_bot_cleanup(
    full_name: str,
    access_token: str,
    branch: str,
    commit_slug: str,
) -> None:
    """Create a pull request and close any existing bot PRs from docs_* branches."""
    BOT_NAME = "docs-bot"
    BOT_EMAIL = "bot@driverai.com"

    print("Checking for existing bot pull requests...")
    try:
        existing_prs = list_pull_requests(full_name, access_token)

        for pr in existing_prs:
            source_branch = pr["head"]["ref"]
            if source_branch.startswith("docs_"):
                pr_id = pr["id"]
                commits = get_pull_request_commits(full_name, pr_id, access_token)

                is_bot_pr = any(
                    commit["commit"]["author"]["name"] == BOT_NAME
                    or commit["commit"]["author"]["email"] == BOT_EMAIL
                    for commit in commits
                )
                if is_bot_pr:
                    close_pull_request(full_name, pr_id, access_token)

    except httpx.HTTPError as e:
        print(f"Error checking for existing bot PRs: {e}")


def create_pull_request(
    full_name: str, branch: str, access_token: str, commit_slug: str
) -> None:
    """Create a pull request for the driver docs changes."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    # First check for existing PRs for this branch
    with httpx.Client() as client:
        # Get existing PRs
        default_branch = fetch_github_default_branch_name(full_name, access_token)
        response = client.get(
            f"https://api.github.com/repos/{full_name}/pulls",
            headers=headers,
            params={"state": "open", "head": f"{full_name.split('/')[0]}:{branch}"},
        )
        response.raise_for_status()

        # Create new PR if none exists
        logo_image = '<img src="https://raw.githubusercontent.com/driver-ai/driver-assets/main/gray_wordmark.svg" width="100px" />'
        pr_data = {
            "title": f"Update driver docs for commit {commit_slug}",
            "body": f"Automated update of driver documentation for commit {commit_slug}\n<br/>\n{logo_image}",
            "head": branch,
            "base": default_branch,
        }

        try:
            response = client.post(
                f"https://api.github.com/repos/{full_name}/pulls",
                headers=headers,
                json=pr_data,
            )
            response.raise_for_status()
            print(f"✅ Created PR: {response.json()['html_url']}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                print("⚠️ No changes to create PR for - branch is up to date with main")
            else:
                raise
