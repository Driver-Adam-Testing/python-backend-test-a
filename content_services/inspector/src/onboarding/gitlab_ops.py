import hashlib
import logging
import os
from uuid import UUID

import requests
from database.models import VcsAutoUpdatePolicy
from onboarding.onboard_utils import AccessTokenError, upload_to_s3_with_metadata
from onboarding.vcs_utils import (
    AuthorInfo,
    BranchInfo,
    CommitInfo,
    RepoInfo,
    VersionControlInfo,
)
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

# TODO: add fetch_github_default_branch_name
# TODO: update generate_codebase_metadata to include installation_id
# TODO: update download_and_upload_repo match gh_ops:download_and_upload_repo
# TODO: add get_repo_clone_info_from_id like in gh_ops

logger = logging.getLogger(__name__)


def fetch_access_token(installation_id: str) -> str:
    print(f"Fetching group access token for installation ID {installation_id}")
    install_key = format_secret_name("GIT_PROVIDER_GAT_INSTALL_SECRET", installation_id)
    secrets_manager = AWSSecretManagementStrategy(
        AWSClientConfig(
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
    )
    secret_value = secrets_manager.read_secret(install_key)
    if not secret_value:
        raise AccessTokenError("Access token not found")

    group_access_tokens = secret_value["token"]

    return group_access_tokens


def download_repo(base_url: str, repo_id: str, commit: str, access_token: str) -> bytes:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{base_url}/api/v4/projects/{repo_id}/repository/archive.zip?sha={commit}",
        headers=headers,
        timeout=120,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.content


def fetch_vcs_info(
    base_url: str, repo_id: str, access_token: str, commit_sha: str | None = None
) -> VersionControlInfo:
    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch repository information
    repo_response = requests.get(
        f"{base_url}/api/v4/projects/{repo_id}",
        headers=headers,
        timeout=120,
    )
    repo_response.raise_for_status()
    repo_data = repo_response.json()
    logger.info(
        f"Repo information retrieved from GitLab API (status code {repo_response.status_code}): {repo_data}"
    )

    default_branch = repo_data["default_branch"]

    # Fetch detailed commit information
    commit_response = requests.get(
        f"{base_url}/api/v4/projects/{repo_id}/repository/commits/{commit_sha}",
        headers=headers,
        timeout=120,
    )
    commit_response.raise_for_status()
    commit_data = commit_response.json()
    logger.info(
        f"Commit data retrieved from GitLab API (status code {commit_response.status_code}): {commit_data}"
    )

    # Build VersionControlInfo
    author_info = AuthorInfo(
        email=commit_data["author_email"],
        name=commit_data["author_name"],
        date=commit_data["authored_date"],
    )

    commit_info = CommitInfo(
        sha=commit_data["id"],
        message=commit_data["message"],
        url=commit_data["web_url"],
        author=author_info,
    )

    branch_info = BranchInfo(name=default_branch)

    repo_info = RepoInfo(
        name=repo_data["name"],
        namespace=repo_data["namespace"]["name"],
        full_name=repo_data["name_with_namespace"],
        url=repo_data["web_url"],
    )

    return VersionControlInfo(
        repository=repo_info,
        commit=commit_info,
        branch=branch_info,
    )


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


def download_and_upload_repo(
    org_id: str, repo: dict, access_token: str, is_push: bool = False
) -> str | None:
    from database.db import engine
    from database.models import (
        GitProviderAppInstallation,
        PrimaryAsset,
        Version,
    )
    from database.models_enums import (
        PrimaryAssetKind,
        PrimaryAssetProvider,
        VersionStatus,
    )
    from sqlalchemy.exc import IntegrityError

    repo_id = repo["metadata"]["id"]
    repo_name = repo["repo_name"]
    commit = repo["latest_commit"]["commit"]["id"]
    installation_id = repo["installation_id"]

    try:
        with Session(engine) as session, session.begin():
            app_install = session.exec(
                select(GitProviderAppInstallation).where(
                    GitProviderAppInstallation.id == installation_id
                )
            ).one()
            base_url = app_install.git_provider_app.base_url

            vcs_info = fetch_vcs_info(
                base_url=base_url,
                repo_id=repo_id,
                access_token=access_token,
                commit_sha=commit,
            )

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
                                f"Generation already in progress for {repo.get('repo_name', 'unknown')}. "
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
                            #     status=VersionStatus.GENERATING,
                            #     # Immediately jump to generating. This signals run_codebase_connection to start inspection after connection
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
                        f"Version already in connecting state for {repo_name}, skipping..."
                    )
                    return repo
                else:
                    # TODO: any other cases to handle explicitly?
                    return repo

            else:
                primary_asset = PrimaryAsset(
                    display_name=repo_name,
                    organization_id=org_id,
                    kind=PrimaryAssetKind.CODEBASE,
                    repository_id=repo_id,
                    installation_id=installation_id,
                    codebase_settings_auto_commit_docs=False,
                    provider=PrimaryAssetProvider.GITLAB_SELF_MANAGED,
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
                    f"Creating primary asset and version for {repo_name}:{commit} for org: {org_id}. Version ID: {version_id}"
                )
    except IntegrityError:
        print(
            f"Failed to create primary asset and version {repo_name}:{commit} for org: {org_id}"
        )
        return repo
    full_repo_name = repo["metadata"]["path_with_namespace"]
    # TODO: update this with additional metadata
    metadata = generate_codebase_metadata(
        org_id,
        full_repo_name,
        repo_id,
        "gitlab_enterprise_self_managed",
        version_id,
        repo_name,
        installation_id,
    )

    zip_content = download_repo(base_url, repo_id, commit, access_token)
    print("Repository downloaded successfully. Size: %d bytes", len(zip_content))

    org_hashed_id = hashlib.sha256(org_id.encode("utf-8")).hexdigest()[:63]
    upload_key = (
        f"assets/{org_hashed_id}/{primary_asset_id}/{version_id}/{repo_name}.zip"
    )
    upload_to_s3_with_metadata(zip_content, metadata, upload_key)
    print(f"Repository {repo_name} uploaded successfully to {upload_key}.")

    return None


def fetch_gitlab_default_branch_name(
    base_url: str, repo_id: str, access_token: str
) -> str:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{base_url}/api/v4/projects/{repo_id}",
        headers=headers,
        timeout=120,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.json()["default_branch"]


def get_repo_clone_info_from_id(
    base_url: str, repo_id: str, access_token: str
) -> tuple[str, str]:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{base_url}/api/v4/projects/{repo_id}",
        headers=headers,
        timeout=120,
        allow_redirects=True,
    )
    response.raise_for_status()
    clone_url = response.json()["http_url_to_repo"]
    full_name = response.json()["path_with_namespace"]
    username = get_gitlab_username(base_url, access_token)
    if clone_url and username:
        clone_url = (
            clone_url.replace("https://", f"https://{username}:{access_token}@")
            if clone_url.startswith("https")
            else clone_url.replace("http://", f"https://{username}:{access_token}@")
        )
    else:
        raise ValueError("Clone URL or username is missing")
    return clone_url, full_name


def create_pull_request(
    base_url: str,
    repo_id: str,
    access_token: str,
    branch: str,
    commit_slug: str,
) -> None:
    default_branch = fetch_gitlab_default_branch_name(base_url, repo_id, access_token)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        f"{base_url}/api/v4/projects/{repo_id}/merge_requests",
        headers=headers,
        json={
            "source_branch": branch,
            "target_branch": default_branch,
            "title": f"Update driver docs for commit {commit_slug}",
        },
    )
    response.raise_for_status()
    print(f"Pull request created successfully: {response.json()['web_url']}")


def get_gitlab_username(base_url: str, access_token: str) -> str:
    url = f"{base_url.rstrip('/')}/api/v4/user"
    headers = {"PRIVATE-TOKEN": access_token}
    print(f"Fetching GitLab username from {url}")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(response.json())
    return response.json()["username"]
