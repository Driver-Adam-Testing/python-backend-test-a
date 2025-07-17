import hashlib
import os
from datetime import UTC, datetime
from uuid import UUID

import modal
import requests
from onboarding.onboard_utils import AccessTokenError, upload_to_s3_with_metadata
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select


def fetch_access_token(installation_id: str) -> str:
    """Fetch Workspace Access Token for Bitbucket installation"""
    print(f"Fetching workspace access token for installation ID {installation_id}")
    install_key = format_secret_name("GIT_PROVIDER_WAT_INSTALL_SECRET", installation_id)
    secrets_manager = AWSSecretManagementStrategy(
        AWSClientConfig(
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
    )
    secret_value = secrets_manager.read_secret(install_key)
    if not secret_value:
        raise AccessTokenError("Workspace access token not found")

    # Handle both old format (direct token) and new format (dict)
    if isinstance(secret_value, str):
        return secret_value

    return secret_value["token"]


def get_default_branch(workspace: str, repo_slug: str, access_token: str) -> str:
    """Get the default branch name for a repository"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    # Default branch info is in mainbranch.name
    return data.get("mainbranch", {}).get("name", "main")


def download_repo(
    workspace: str, repo_slug: str, commit: str, access_token: str
) -> bytes:
    """Download Bitbucket repository using git clone"""
    import shutil
    import subprocess
    import tempfile
    import zipfile
    from pathlib import Path

    print(
        f"Using git clone to download repository {workspace}/{repo_slug} at commit {commit}"
    )

    # Create a temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / repo_slug

        # Clone URL with x-token-auth and the access token
        # Format: https://x-token-auth:{token}@bitbucket.org/{workspace}/{repo_slug}.git
        clone_url = f"https://x-token-auth:{access_token}@bitbucket.org/{workspace}/{repo_slug}.git"

        try:
            # Try to clone with shallow depth at specific commit
            print(f"Attempting to clone repository at commit {commit}...")

            # First, try a shallow clone of the specific commit
            clone_cmd = [
                "git",
                "clone",
                "--no-checkout",  # Don't checkout files yet
                clone_url,
                str(repo_path),
            ]

            clone_result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if clone_result.returncode != 0:
                print(f"Clone failed: {clone_result.stderr}")
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")

            print("Repository cloned successfully, checking out specific commit...")

            # Checkout the specific commit
            checkout_result = subprocess.run(
                ["git", "checkout", commit],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
            )

            if checkout_result.returncode != 0:
                print(
                    f"Warning: Could not checkout commit {commit}: {checkout_result.stderr}"
                )
                # Try fetching the commit first
                print("Fetching all commits and trying again...")

                subprocess.run(
                    ["git", "fetch", "--unshallow"],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                )

                # Try checkout again
                checkout_result = subprocess.run(
                    ["git", "checkout", commit],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                )

                if checkout_result.returncode != 0:
                    print(
                        f"Failed to checkout commit {commit}: {checkout_result.stderr}"
                    )
                    raise Exception(f"Failed to checkout commit {commit}")

            print(f"Successfully checked out commit {commit}")

            # Remove .git directory to reduce size
            git_dir = repo_path / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)

            # Create a zip archive
            zip_path = Path(temp_dir) / f"{repo_slug}.zip"
            print("Creating zip archive...")

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Walk through all files and add them to the zip
                for file_path in repo_path.rglob("*"):
                    if file_path.is_file():
                        # Get the relative path from the repo root
                        arcname = file_path.relative_to(repo_path)
                        zipf.write(file_path, arcname)

            # Read the zip file content
            with open(zip_path, "rb") as f:
                zip_content = f.read()

            print(f"Archive created successfully. Size: {len(zip_content)} bytes")
            return zip_content

        except subprocess.TimeoutExpired:
            raise Exception("Git clone operation timed out")
        except Exception as e:
            print(f"Error during repository download: {e!s}")
            raise


def get_latest_commit(workspace: str, repo_slug: str, access_token: str) -> str:
    """Get latest commit SHA for main branch"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/commits"

    response = requests.get(url, headers=headers, params={"pagelen": 1})
    response.raise_for_status()

    commits = response.json().get("values", [])
    if commits:
        return commits[0]["hash"]
    raise ValueError("No commits found")


def generate_codebase_metadata(
    org_id: str,
    workspace: str,
    repo_name: str,
    repo_id: str | int,
    provider: str,
    version_id: str | UUID,
    asset_name: str,
    install_id: str,
) -> dict:
    from database.models_v2_enums import PrimaryAssetKind

    return {
        "unhashed_organization_id": org_id,
        "workspace": workspace,
        "provider": provider,
        "version_id": str(version_id),
        "repository_id": str(repo_id),
        "asset_name": asset_name,
        "asset_kind": PrimaryAssetKind.CODEBASE,
        "install_id": install_id,
    }


def download_and_upload_repo(
    org_id: str, repo: dict, access_token: str, is_push: bool = False
) -> str | None:
    """Download and upload Bitbucket repository"""
    from database.db import engine
    from database.models_v1 import (
        InspectorRun,
        UsageEvent,
        UsageEventType,
        UsageSession,
    )
    from database.models_v2 import (
        PrimaryAsset,
        Version,
    )
    from database.models_v2_enums import (
        PrimaryAssetKind,
        VersionStatus,
    )
    from sqlalchemy.exc import IntegrityError

    # Handle different repo dict structures
    # From GitRepository model or from webhook
    metadata = repo.get("metadata", {})
    repo_id = repo.get("repo_id") or metadata.get("id") or metadata.get("uuid")
    repo_name = repo.get("repo_name") or repo.get("name")
    workspace = metadata.get("workspace") or repo.get("workspace")
    repo_slug = metadata.get("slug") or repo.get("slug")

    # Handle missing fields
    if not repo_id:
        print(f"Missing repo_id in repo data: {repo}")
        return repo_name
    if not repo_name:
        print(f"Missing repo_name in repo data: {repo}")
        return "unknown"
    if not workspace:
        print(f"Missing workspace in repo data: {repo}")
        return repo_name
    if not repo_slug:
        print(f"Missing repo slug in repo data: {repo}")
        return repo_name

    # Get latest commit if not provided
    commit = None
    if repo.get("latest_commit"):
        if isinstance(repo["latest_commit"], dict):
            commit = repo["latest_commit"].get("id") or repo["latest_commit"].get(
                "commit", {}
            ).get("id")
        else:
            commit = repo["latest_commit"]

    if not commit:
        try:
            commit = get_latest_commit(workspace, repo_slug, access_token)
        except Exception as e:
            print(f"Failed to get latest commit for {repo_name}: {e}")
            return repo_name

    installation_id = repo.get("installation_id")
    if not installation_id:
        print(f"Missing installation_id for repo {repo_name}")
        return repo_name

    try:
        with Session(engine) as session, session.begin():
            if is_push:
                primary_asset = session.exec(
                    select(PrimaryAsset)
                    .where(
                        PrimaryAsset.organization_id == org_id,
                        PrimaryAsset.repository_id == repo_id,
                    )
                    .options(selectinload(PrimaryAsset.versions))
                ).first()
                if not primary_asset:
                    print(
                        f"Failed to find primary asset for {repo_name} for org: {org_id}, unable to process push event"
                    )
                    return repo_name
                primary_asset_id = primary_asset.id

                # Handle version creation based on current status
                if all(
                    v.status == VersionStatus.CONNECTED for v in primary_asset.versions
                ):
                    new_version = Version(
                        primary_asset_id=primary_asset.id,
                        display_name=commit,
                        status=VersionStatus.CONNECTING,
                        previous_version_id=primary_asset.versions[0].id
                        if primary_asset.versions
                        else None,
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
                    # Handle existing generating versions
                    for version in primary_asset.versions:
                        if version.status in [
                            VersionStatus.GENERATION_COMPLETE,
                            VersionStatus.GENERATION_ERROR,
                        ]:
                            new_version = Version(
                                primary_asset_id=primary_asset.id,
                                display_name=commit,
                                status=VersionStatus.GENERATING,
                                previous_version_id=version.id,
                            )
                            session.add(new_version)
                            version_id = new_version.id
                            break
                        elif version.status == VersionStatus.GENERATING:
                            # Cancel existing run and create new version
                            run_statement = (
                                select(InspectorRun)
                                .where(InspectorRun.version_id == version.id)
                                .order_by(InspectorRun.created_at.desc())
                            )
                            run = session.exec(run_statement).first()

                            if run is not None:
                                call_id = run.call_id
                                modal_call = modal.FunctionCall.from_id(call_id)
                                modal_call.cancel()

                            session.delete(version)

                            # Handle usage credits
                            usage_session_statement = (
                                select(UsageSession)
                                .join(
                                    UsageEvent, UsageSession.id == UsageEvent.session_id
                                )
                                .where(
                                    UsageSession.session_metadata["version_id"].astext
                                    == str(version.id)
                                )
                                .where(
                                    UsageEvent.event_type
                                    == UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT
                                )
                                .options(selectinload(UsageSession.usage_events))
                            )
                            usage_session = session.exec(
                                usage_session_statement
                            ).first()

                            if usage_session is not None:
                                usage_event = next(
                                    (
                                        event
                                        for event in usage_session.usage_events
                                        if event.event_type
                                        == UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT.value
                                    ),
                                    None,
                                )
                                if usage_event is not None:
                                    new_usage_session = UsageSession(
                                        status=usage_session.status,
                                        organization_id=usage_session.organization_id,
                                        user_id="SYSTEM",
                                        session_metadata=usage_session.session_metadata,
                                    )
                                    session.add(new_usage_session)
                                    usage_event_credit = UsageEvent(
                                        **usage_event.dict(
                                            exclude={
                                                "id",
                                                "bytes_in",
                                                "session_id",
                                                "timestamp",
                                                "event_type",
                                            }
                                        ),
                                        event_type=UsageEventType.ADDITIONAL_PLATFORM_USAGE_CREDIT,
                                        session_id=new_usage_session.id,
                                        bytes_in=abs(usage_event.bytes_in),
                                        timestamp=datetime.now(tz=UTC),
                                    )
                                    session.add(usage_event_credit)

                            new_version = Version(
                                primary_asset_id=primary_asset.id,
                                display_name=commit,
                                status=VersionStatus.GENERATING,
                                previous_version_id=version.previous_version_id,
                            )
                            session.add(new_version)
                            version_id = new_version.id
                            print(
                                f"Version already in generating state for {repo_name}, deleting existing version and restarting inspection with new version..."
                            )
                            break
                elif (
                    primary_asset.versions
                    and primary_asset.versions[0].status == VersionStatus.CONNECTING
                ):
                    print(
                        f"Version already in connecting state for {repo_name}, skipping..."
                    )
                    return repo_name
                else:
                    return repo_name
            else:
                # Create new primary asset and version
                primary_asset = PrimaryAsset(
                    display_name=repo_name,
                    organization_id=org_id,
                    kind=PrimaryAssetKind.CODEBASE,
                    repository_id=repo_id,
                    installation_id=installation_id,
                    codebase_settings_auto_commit_docs=False,
                )
                session.add(primary_asset)
                primary_asset_id = primary_asset.id

                version = Version(
                    primary_asset_id=primary_asset.id,
                    display_name=commit,
                    status=VersionStatus.CONNECTING,
                    previous_version_id=None,
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
        return repo_name

    # Generate metadata
    metadata = generate_codebase_metadata(
        org_id,
        workspace,
        repo_name,
        repo_id,
        "bitbucket",
        version_id,
        repo_name,
        installation_id,
    )

    # Download repository
    try:
        zip_content = download_repo(workspace, repo_slug, commit, access_token)
        print(f"Repository downloaded successfully. Size: {len(zip_content)} bytes")
    except Exception as e:
        print(f"Failed to download repository {repo_name}: {e}")
        return repo_name

    # Upload to S3
    org_hashed_id = hashlib.sha256(org_id.encode("utf-8")).hexdigest()[:63]
    upload_key = (
        f"assets/{org_hashed_id}/{primary_asset_id}/{version_id}/{repo_name}.zip"
    )
    upload_to_s3_with_metadata(zip_content, metadata, upload_key)
    print(f"Repository {repo_name} uploaded successfully to {upload_key}.")

    return None


def get_repo_clone_info_from_id(
    workspace: str, repo_slug: str, access_token: str
) -> tuple[str, str]:
    """Get repository clone URL and full name"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    full_name = data["full_name"]

    # Get clone URL from links
    clone_links = data.get("links", {}).get("clone", [])
    https_link = next((link for link in clone_links if link["name"] == "https"), None)

    if not https_link:
        raise ValueError("HTTPS clone URL not found")

    clone_url = https_link["href"]
    # Insert token into URL
    if clone_url.startswith("https://"):
        clone_url = clone_url.replace(
            "https://", f"https://x-token-auth:{access_token}@"
        )

    return clone_url, full_name


def fetch_bitbucket_default_branch_name(
    workspace: str, repo_slug: str, access_token: str
) -> str:
    """Fetch default branch name for Bitbucket repository"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    return data.get("mainbranch", {}).get("name", "main")


def create_pull_request(
    workspace: str,
    repo_slug: str,
    access_token: str,
    branch: str,
    commit_slug: str,
) -> None:
    """Create a pull request for Bitbucket"""
    default_branch = fetch_bitbucket_default_branch_name(
        workspace, repo_slug, access_token
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    pr_data = {
        "title": f"Update driver docs for commit {commit_slug}",
        "description": f"Automated update of driver documentation for commit {commit_slug}",
        "source": {"branch": {"name": branch}},
        "destination": {"branch": {"name": default_branch}},
        "close_source_branch": False,
    }

    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests"
    response = requests.post(url, headers=headers, json=pr_data)

    try:
        response.raise_for_status()
        print(
            f"Pull request created successfully: {response.json()['links']['html']['href']}"
        )
    except requests.HTTPError as e:
        if e.response.status_code == 400:
            error_detail = e.response.json()
            if "already exists" in str(error_detail):
                print("⚠️ Pull request already exists for this branch")
            else:
                raise
        else:
            raise
