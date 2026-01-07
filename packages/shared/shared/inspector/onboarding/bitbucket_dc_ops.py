import hashlib
import logging
import os
import shutil
import ssl
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import httpx
from database.models import Organization, PrimaryAssetRoleGrant
from database.models_enums import (
    PrimaryAssetKind,
    PrimaryAssetProvider,
    PrimaryAssetRole,
    PrincipalKind,
    SourceVisibility,
    VcsAutoUpdatePolicy,
    VersionStatus,
)
from shared.inspector.onboarding.onboard_utils import (
    AccessTokenError,
    upload_to_s3_with_metadata,
)
from shared.inspector.onboarding.vcs_utils import (
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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

# Secret prefix for Bitbucket DC installations
BBDC_SECRET_PREFIX = "GIT_PROVIDER_BBDC_HTTP_INSTALL_SECRET"

# Environment variable to override instance URL (for Docker/local dev)
BBDC_INSTANCE_URL_ENV = "BITBUCKET_DC_INSTANCE_URL"


def _create_git_provider_grants(
    session: Session,
    primary_asset_id: UUID,
    organization_id: str,
) -> None:
    """Create default grants for a primary asset based on org visibility settings."""
    org = session.get(Organization, organization_id)
    if not org:
        raise ValueError(f"Organization {organization_id} not found")

    visibility = org.default_source_visibility

    if visibility == SourceVisibility.internal:
        grant = PrimaryAssetRoleGrant(
            primary_asset_id=primary_asset_id,
            organization_id=organization_id,
            principal_kind=PrincipalKind.org,
            role=PrimaryAssetRole.asset_member,
        )
        session.add(grant)
        print(f"INFO: Created internal visibility grant for asset {primary_asset_id}")
    elif visibility == SourceVisibility.public:
        grant = PrimaryAssetRoleGrant(
            primary_asset_id=primary_asset_id,
            organization_id=organization_id,
            principal_kind=PrincipalKind.public,
            role=PrimaryAssetRole.asset_member,
        )
        session.add(grant)
        print(f"INFO: Created public visibility grant for asset {primary_asset_id}")


def fetch_access_token(installation_id: str) -> tuple[str, str]:
    """Fetch HTTP Access Token and instance URL for installation.

    Returns:
        Tuple of (token, instance_url). The instance_url can be overridden
        by the BITBUCKET_DC_INSTANCE_URL environment variable for local
        development or Docker environments.
    """
    print(
        f"Fetching HTTP Access Token for Bitbucket DC installation ID {installation_id}"
    )
    install_key = format_secret_name(BBDC_SECRET_PREFIX, installation_id)
    secrets_manager = AWSSecretManagementStrategy(
        AWSClientConfig(
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
    )
    secret_value = secrets_manager.read_secret(install_key)
    if not secret_value:
        raise AccessTokenError(
            "HTTP Access Token not found for Bitbucket DC installation"
        )

    # Allow environment variable to override instance URL for Docker/local dev
    instance_url = os.environ.get(BBDC_INSTANCE_URL_ENV) or secret_value["instance_url"]

    return (
        secret_value["token"],
        instance_url,
    )


def fetch_secrets(installation_id: str) -> dict:
    """Fetch all secrets for installation.

    The instance_url in the returned dict can be overridden by the
    BITBUCKET_DC_INSTANCE_URL environment variable for local development
    or Docker environments.
    """
    install_key = format_secret_name(BBDC_SECRET_PREFIX, installation_id)
    secrets_manager = AWSSecretManagementStrategy(
        AWSClientConfig(
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
    )
    secret_value = secrets_manager.read_secret(install_key)
    if not secret_value:
        raise AccessTokenError("Secrets not found for Bitbucket DC installation")

    # Allow environment variable to override instance URL for Docker/local dev
    env_url = os.environ.get(BBDC_INSTANCE_URL_ENV)
    if env_url:
        secret_value = dict(secret_value)  # Copy to avoid mutating cached value
        secret_value["instance_url"] = env_url

    return secret_value


def _get_ssl_context(secrets: dict) -> bool | ssl.SSLContext:
    """Get SSL context based on secrets configuration."""
    if secrets.get("disable_ssl_verify", False):
        return False
    if secrets.get("ca_bundle_path"):
        context = ssl.create_default_context()
        context.load_verify_locations(secrets["ca_bundle_path"])
        return context
    return True


def build_clone_url(
    instance_url: str,
    project_key: str,
    repo_slug: str,
) -> str:
    """Build clone URL for Bitbucket Data Center (without embedded credentials).

    For Bitbucket DC HTTP Access Tokens (Project/Repository tokens), credentials
    must be passed via git header, not embedded in URL.
    Format: https://{host}/scm/{project}/{slug}.git

    The token is passed separately via: git clone -c http.extraHeader='Authorization: Bearer TOKEN'
    """
    parsed = urlparse(instance_url)
    host = parsed.netloc
    scheme = parsed.scheme
    return f"{scheme}://{host}/scm/{project_key}/{repo_slug}.git"


def get_default_branch(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    access_token: str,
    verify: bool | ssl.SSLContext = True,
) -> str:
    """Get default branch for repository.

    First tries the /default-branch endpoint, then validates the branch exists.
    Falls back to checking branches list for isDefault flag or first available branch.
    """
    api_base = f"{instance_url.rstrip('/')}/rest/api/1.0"
    headers = {"Authorization": f"Bearer {access_token}"}

    with httpx.Client(verify=verify, timeout=30.0) as client:
        # First, try the default-branch endpoint
        default_branch = None
        try:
            url = f"{api_base}/projects/{project_key}/repos/{repo_slug}/default-branch"
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            default_branch = data.get("displayId")
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise
            logger.warning(
                f"Default branch endpoint returned 404 for {project_key}/{repo_slug}"
            )

        # Validate the default branch exists by listing branches
        branches_url = f"{api_base}/projects/{project_key}/repos/{repo_slug}/branches"
        try:
            response = client.get(branches_url, headers=headers, params={"limit": 100})
            response.raise_for_status()
            branches_data = response.json()
            branches = branches_data.get("values", [])

            if not branches:
                logger.warning(f"No branches found for {project_key}/{repo_slug}")
                return default_branch or "main"

            # Check if reported default branch actually exists
            if default_branch:
                for b in branches:
                    if b.get("displayId") == default_branch:
                        return default_branch
                logger.warning(
                    f"Default branch '{default_branch}' not found in branches list"
                )

            # Look for branch with isDefault flag
            for b in branches:
                if b.get("isDefault"):
                    actual_default = b.get("displayId")
                    logger.info(f"Using isDefault branch: {actual_default}")
                    return actual_default

            # Fall back to first branch
            first_branch = branches[0].get("displayId")
            logger.info(f"No default found, using first branch: {first_branch}")
            return first_branch

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list branches: {e}")
            return default_branch or "main"


def get_latest_commit_on_branch(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    branch: str,
    access_token: str,
    verify: bool | ssl.SSLContext = True,
) -> str | None:
    """Get the latest commit SHA on a branch.

    Returns None if the repository has no commits (empty repo).
    """
    api_base = f"{instance_url.rstrip('/')}/rest/api/1.0"
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{api_base}/projects/{project_key}/repos/{repo_slug}/branches"

    try:
        with httpx.Client(verify=verify, timeout=30.0) as client:
            # First try with filter
            response = client.get(
                url, headers=headers, params={"filterText": branch, "limit": 10}
            )
            response.raise_for_status()
            data = response.json()
            branches = data.get("values", [])

            # Find the exact branch match
            for b in branches:
                if b.get("displayId") == branch:
                    return b.get("latestCommit")

            # If no match with filter, try listing all branches
            if not branches:
                response = client.get(url, headers=headers, params={"limit": 100})
                response.raise_for_status()
                data = response.json()
                branches = data.get("values", [])

            # Find the exact branch match
            for b in branches:
                if b.get("displayId") == branch:
                    return b.get("latestCommit")

            # Fallback: use default branch or first available branch
            for b in branches:
                if b.get("isDefault"):
                    print(
                        f"Using default branch {b.get('displayId')} instead of {branch}"
                    )
                    return b.get("latestCommit")

            if branches:
                print(
                    f"Using first available branch {branches[0].get('displayId')} instead of {branch}"
                )
                return branches[0].get("latestCommit")

            # Repository is likely empty (no commits yet)
            print(
                f"No branches found for {project_key}/{repo_slug} - repository may be empty"
            )
            return None

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to get latest commit on {branch}: {e}")
        raise


def download_repo(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    commit: str,
    access_token: str,
    ca_bundle_path: str | None = None,
    disable_ssl_verify: bool = False,
) -> bytes:
    """Download repository using git clone with Bearer token auth.

    For Bitbucket DC Project/Repository tokens, we must use Bearer auth via
    git http.extraHeader, not embedded credentials in the URL.

    Returns:
        ZIP file content as bytes
    """
    print(
        f"Cloning Bitbucket DC repository {project_key}/{repo_slug} at commit {commit}"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / repo_slug

        clone_url = build_clone_url(instance_url, project_key, repo_slug)

        # Set up environment for SSL handling
        env = os.environ.copy()
        if disable_ssl_verify:
            env["GIT_SSL_NO_VERIFY"] = "true"
        elif ca_bundle_path:
            env["GIT_SSL_CAINFO"] = ca_bundle_path

        try:
            # Clone the repository with Bearer token via http.extraHeader
            # This is required for Bitbucket DC Project/Repository HTTP Access Tokens
            print("Cloning repository...")
            clone_cmd = [
                "git",
                "-c",
                f"http.extraHeader=Authorization: Bearer {access_token}",
                "clone",
                "--no-checkout",
                clone_url,
                str(repo_path),
            ]

            clone_result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )

            if clone_result.returncode != 0:
                print(f"Clone failed: {clone_result.stderr}")
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")

            print("Repository cloned successfully")

            # Checkout specific commit or HEAD if no commit specified
            if commit:
                print(f"Checking out commit {commit}...")
                checkout_result = subprocess.run(
                    ["git", "checkout", commit],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    env=env,
                )

                if checkout_result.returncode != 0:
                    print(
                        f"Could not checkout commit {commit}, fetching all commits..."
                    )
                    subprocess.run(
                        ["git", "fetch", "--unshallow"],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        env=env,
                    )

                    checkout_result = subprocess.run(
                        ["git", "checkout", commit],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        env=env,
                    )

                    if checkout_result.returncode != 0:
                        raise Exception(f"Failed to checkout commit {commit}")

                print(f"Successfully checked out commit {commit}")
            else:
                # No specific commit, checkout the default branch
                # After --no-checkout clone, use `git checkout` with no args to checkout default branch
                print("No commit specified, checking out default branch...")
                checkout_result = subprocess.run(
                    ["git", "checkout"],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if checkout_result.returncode != 0:
                    raise Exception(
                        f"Failed to checkout default branch: {checkout_result.stderr}"
                    )

                # Get the HEAD commit SHA for logging
                head_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    env=env,
                )
                head_sha = (
                    head_result.stdout.strip()
                    if head_result.returncode == 0
                    else "unknown"
                )
                print(f"Successfully checked out default branch (HEAD: {head_sha})")

            # Remove .git directory
            git_dir = repo_path / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)

            # Create ZIP archive
            zip_path = Path(temp_dir) / f"{repo_slug}.zip"
            print("Creating ZIP archive...")

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in repo_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(repo_path)
                        zipf.write(file_path, arcname)

            with open(zip_path, "rb") as f:
                zip_content = f.read()

            print(f"Archive created. Size: {len(zip_content)} bytes")
            return zip_content

        except subprocess.TimeoutExpired:
            raise Exception("Git clone operation timed out")
        except Exception as e:
            print(f"Error during repository download: {e!s}")
            raise


def get_commit_info(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    commit_sha: str,
    access_token: str,
    verify: bool | ssl.SSLContext = True,
) -> dict:
    """Get commit details from Bitbucket DC API."""
    api_base = f"{instance_url.rstrip('/')}/rest/api/1.0"
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{api_base}/projects/{project_key}/repos/{repo_slug}/commits/{commit_sha}"

    with httpx.Client(verify=verify, timeout=30.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def get_repository_info(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    access_token: str,
    verify: bool | ssl.SSLContext = True,
) -> dict:
    """Get repository details from Bitbucket DC API."""
    api_base = f"{instance_url.rstrip('/')}/rest/api/1.0"
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{api_base}/projects/{project_key}/repos/{repo_slug}"

    with httpx.Client(verify=verify, timeout=30.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def fetch_vcs_info(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    access_token: str,
    commit_sha: str,
    tracked_branch: str | None = None,
    verify: bool | ssl.SSLContext = True,
) -> VersionControlInfo:
    """Fetch version control information for a repository."""
    # Get repository info
    repo_data = get_repository_info(
        instance_url, project_key, repo_slug, access_token, verify
    )

    # Get default branch if not tracking specific branch
    if tracked_branch is None:
        tracked_branch = get_default_branch(
            instance_url, project_key, repo_slug, access_token, verify
        )

    # Get commit info
    commit_data = get_commit_info(
        instance_url, project_key, repo_slug, commit_sha, access_token, verify
    )

    # Build VersionControlInfo
    author_info = AuthorInfo(
        email=commit_data.get("author", {}).get("emailAddress", ""),
        name=commit_data.get("author", {}).get("name", ""),
        date=str(commit_data.get("authorTimestamp", "")),
    )

    # Build repo URL
    repo_url = f"{instance_url}/projects/{project_key}/repos/{repo_slug}"

    commit_info = CommitInfo(
        sha=commit_data.get("id", commit_sha),
        message=commit_data.get("message", ""),
        url=f"{repo_url}/commits/{commit_sha}",
        author=author_info,
    )

    branch_info = BranchInfo(name=tracked_branch)

    repo_info = RepoInfo(
        name=repo_data.get("name", repo_slug),
        namespace=project_key,
        full_name=f"{project_key}/{repo_slug}",
        url=repo_url,
    )

    return VersionControlInfo(
        repository=repo_info,
        commit=commit_info,
        branch=branch_info,
    )


def generate_codebase_metadata(
    org_id: str,
    project_key: str,
    repo_name: str,
    repo_id: str | int,
    version_id: str | UUID,
    asset_name: str,
    install_id: str,
    instance_url: str,
) -> dict:
    """Generate metadata for codebase upload."""
    return {
        "unhashed_organization_id": org_id,
        "full_repo_name": f"{project_key}/{repo_name}",
        "project_key": project_key,
        "provider": "bitbucket_data_center",
        "version_id": str(version_id),
        "repository_id": str(repo_id),
        "asset_name": asset_name,
        "asset_kind": PrimaryAssetKind.CODEBASE,
        "install_id": install_id,
        "instance_url": instance_url,
    }


def download_and_upload_repo(
    org_id: str, repo: dict, access_token: str, is_push: bool = False
) -> str | None:
    """Download and upload Bitbucket DC repository."""
    from database.db import engine
    from database.models import PrimaryAsset, Version

    # Extract repo info
    metadata = repo.get("metadata", {})
    repo_id = repo.get("repo_id") or metadata.get("id")
    repo_name = repo.get("repo_name") or repo.get("name")
    project_key = repo.get("project_key") or metadata.get("project_key")
    repo_slug = repo.get("repo_slug") or metadata.get("slug") or repo_name
    installation_id = repo.get("installation_id")
    tracked_branch = repo.get("tracked_branch")

    if not installation_id:
        print(f"Missing installation_id for repo {repo_name}")
        return repo_name

    # Get secrets for SSL config and instance_url
    try:
        secrets = fetch_secrets(installation_id)
        verify = _get_ssl_context(secrets)
        ca_bundle_path = secrets.get("ca_bundle_path")
        disable_ssl_verify = secrets.get("disable_ssl_verify", False)
        # Prefer instance_url from secrets over metadata (secrets has the authoritative URL)
        # Note: fetch_secrets applies BITBUCKET_DC_INSTANCE_URL env var override if set
        instance_url = secrets.get("instance_url") or metadata.get("instance_url")
    except Exception as e:
        print(f"Failed to fetch secrets: {e}")
        return repo_name

    if not repo_id or not repo_name or not project_key or not instance_url:
        print(f"Missing required repo data: {repo}")
        return repo_name or "unknown"

    # Get commit
    commit = None
    if repo.get("commit"):
        commit = repo["commit"]
    elif repo.get("latest_commit"):
        if isinstance(repo["latest_commit"], dict):
            commit = repo["latest_commit"].get("id")
        else:
            commit = repo["latest_commit"]

    if not commit:
        # Get latest commit on tracked branch (or default branch)
        branch_to_check = tracked_branch or get_default_branch(
            instance_url, project_key, repo_slug, access_token, verify
        )
        print(
            f"No commit specified, fetching latest commit on branch {branch_to_check}..."
        )
        commit = get_latest_commit_on_branch(
            instance_url, project_key, repo_slug, branch_to_check, access_token, verify
        )
        if not commit:
            print(f"Repository {repo_name} appears to be empty (no commits). Skipping.")
            return repo_name
        print(f"Using commit {commit}")

    # Fetch VCS info
    try:
        vcs_info = fetch_vcs_info(
            instance_url=instance_url,
            project_key=project_key,
            repo_slug=repo_slug,
            access_token=access_token,
            commit_sha=commit,
            tracked_branch=tracked_branch,
            verify=verify,
        )
    except Exception as e:
        print(f"Failed to fetch VCS info: {e}")
        vcs_info = None

    try:
        with Session(engine) as session, session.begin():
            if is_push:
                primary_asset = session.exec(
                    select(PrimaryAsset)
                    .where(
                        PrimaryAsset.organization_id == org_id,
                        PrimaryAsset.repository_id == str(repo_id),
                    )
                    .options(selectinload(PrimaryAsset.versions))
                ).first()

                if not primary_asset:
                    print(f"Primary asset not found for {repo_name}, org: {org_id}")
                    return repo_name

                primary_asset_id = primary_asset.id

                # Handle version creation based on current status
                if all(
                    v.status == VersionStatus.CONNECTED for v in primary_asset.versions
                ):
                    new_version = Version(
                        primary_asset_id=primary_asset.id,
                        vcs_hash=commit,
                        status=VersionStatus.CONNECTING,
                        previous_version_id=primary_asset.versions[0].id
                        if primary_asset.versions
                        else None,
                        vcs_metadata=vcs_info.model_dump() if vcs_info else None,
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
                    for version in primary_asset.versions:
                        if version.status in [
                            VersionStatus.GENERATION_COMPLETE,
                            VersionStatus.GENERATION_ERROR,
                        ]:
                            new_version = Version(
                                primary_asset_id=primary_asset.id,
                                vcs_hash=commit,
                                status=VersionStatus.GENERATING,
                                previous_version_id=version.id,
                                vcs_metadata=vcs_info.model_dump()
                                if vcs_info
                                else None,
                            )
                            session.add(new_version)
                            version_id = new_version.id
                            break
                        elif version.status == VersionStatus.GENERATING:
                            print(
                                f"Generation in progress for {repo_name}, ignoring push"
                            )
                            return repo_name
                elif (
                    primary_asset.versions
                    and primary_asset.versions[0].status == VersionStatus.CONNECTING
                ):
                    print(f"Version already connecting for {repo_name}")
                    return repo_name
                else:
                    return repo_name
            else:
                # Create new primary asset and version
                primary_asset = PrimaryAsset(
                    display_name=repo_name,
                    organization_id=org_id,
                    kind=PrimaryAssetKind.CODEBASE,
                    repository_id=str(repo_id),
                    installation_id=installation_id,
                    codebase_settings_auto_commit_docs=False,
                    provider=PrimaryAssetProvider.BITBUCKET_DATA_CENTER,
                    vcs_auto_update_policy=VcsAutoUpdatePolicy.AFTER_EVERY_COMMIT,
                )
                session.add(primary_asset)
                primary_asset_id = primary_asset.id

                version = Version(
                    primary_asset_id=primary_asset.id,
                    vcs_hash=commit,
                    status=VersionStatus.CONNECTING,
                    previous_version_id=None,
                    vcs_metadata=vcs_info.model_dump() if vcs_info else None,
                )
                session.add(version)
                version_id = version.id

                _create_git_provider_grants(session, primary_asset_id, org_id)

                print(f"Created primary asset and version for {repo_name}:{commit}")

    except IntegrityError:
        print(f"Failed to create primary asset for {repo_name}:{commit}")
        return repo_name

    # Generate metadata
    codebase_metadata = generate_codebase_metadata(
        org_id,
        project_key,
        repo_name,
        repo_id,
        version_id,
        repo_name,
        installation_id,
        instance_url,
    )

    # Download repository
    zip_content = download_repo(
        instance_url=instance_url,
        project_key=project_key,
        repo_slug=repo_slug,
        commit=commit,
        access_token=access_token,
        ca_bundle_path=ca_bundle_path,
        disable_ssl_verify=disable_ssl_verify,
    )
    print(f"Repository downloaded. Size: {len(zip_content)} bytes")

    # Upload to S3
    org_hashed_id = hashlib.sha256(org_id.encode("utf-8")).hexdigest()[:63]
    upload_key = (
        f"assets/{org_hashed_id}/{primary_asset_id}/{version_id}/{repo_name}.zip"
    )
    upload_to_s3_with_metadata(zip_content, codebase_metadata, upload_key)
    print(f"Repository {repo_name} uploaded to {upload_key}")

    return None


def get_repo_clone_info_from_id(
    instance_url: str,
    project_key: str,
    repo_slug: str,
) -> tuple[str, str]:
    """Get repository clone URL and full name.

    Note: The clone URL does not contain credentials. For Bitbucket DC,
    Bearer auth must be passed via git http.extraHeader.
    """
    clone_url = build_clone_url(instance_url, project_key, repo_slug)
    full_name = f"{project_key}/{repo_slug}"
    return clone_url, full_name


# =============================================================================
# Pull Request Functions for Push Bot
# =============================================================================


def list_pull_requests(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    access_token: str,
    state: str = "OPEN",
    verify: bool | ssl.SSLContext = True,
) -> list[dict]:
    """List pull requests for a repository.

    Args:
        instance_url: Bitbucket DC instance URL
        project_key: Project key
        repo_slug: Repository slug
        access_token: HTTP Access Token
        state: PR state filter (OPEN, MERGED, DECLINED, ALL)
        verify: SSL verification setting

    Returns:
        List of pull request dictionaries
    """
    api_base = f"{instance_url.rstrip('/')}/rest/api/1.0"
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{api_base}/projects/{project_key}/repos/{repo_slug}/pull-requests"

    all_prs: list[dict] = []
    start = 0
    limit = 25

    with httpx.Client(verify=verify, timeout=30.0) as client:
        while True:
            params = {"state": state, "start": start, "limit": limit}
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            all_prs.extend(data.get("values", []))

            if data.get("isLastPage", True):
                break

            start = data.get("nextPageStart", start + limit)

    return all_prs


def get_pull_request_commits(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    pr_id: int,
    access_token: str,
    verify: bool | ssl.SSLContext = True,
) -> list[dict]:
    """Get commits for a pull request.

    Args:
        instance_url: Bitbucket DC instance URL
        project_key: Project key
        repo_slug: Repository slug
        pr_id: Pull request ID
        access_token: HTTP Access Token
        verify: SSL verification setting

    Returns:
        List of commit dictionaries
    """
    api_base = f"{instance_url.rstrip('/')}/rest/api/1.0"
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{api_base}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/commits"

    all_commits: list[dict] = []
    start = 0
    limit = 25

    with httpx.Client(verify=verify, timeout=30.0) as client:
        while True:
            params = {"start": start, "limit": limit}
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            all_commits.extend(data.get("values", []))

            if data.get("isLastPage", True):
                break

            start = data.get("nextPageStart", start + limit)

    return all_commits


def decline_pull_request(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    pr_id: int,
    access_token: str,
    verify: bool | ssl.SSLContext = True,
) -> None:
    """Decline (close) a pull request.

    Args:
        instance_url: Bitbucket DC instance URL
        project_key: Project key
        repo_slug: Repository slug
        pr_id: Pull request ID
        access_token: HTTP Access Token
        verify: SSL verification setting
    """
    api_base = f"{instance_url.rstrip('/')}/rest/api/1.0"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # First check the PR status
    pr_url = (
        f"{api_base}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
    )

    with httpx.Client(verify=verify, timeout=30.0) as client:
        pr_response = client.get(pr_url, headers=headers)

        if pr_response.status_code == 200:
            pr_data = pr_response.json()
            state = pr_data.get("state", "").upper()

            if state in ["MERGED", "DECLINED"]:
                print(f"INFO: Pull request #{pr_id} is already {state.lower()}")
                return

            # Get the current version for optimistic locking
            version = pr_data.get("version", 0)

        # Decline the PR
        decline_url = f"{pr_url}/decline"
        params = {"version": version}

        response = client.post(decline_url, headers=headers, params=params)

        try:
            response.raise_for_status()
            print(f"Declined pull request #{pr_id}")
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_json = e.response.json()
                error_detail = f" - {error_json}"
            except Exception:
                error_detail = f" - {e.response.text}"

            print(f"Failed to decline pull request #{pr_id}: {e}{error_detail}")
            raise


def create_pull_request(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    access_token: str,
    source_branch: str,
    commit_slug: str,
    target_branch: str | None = None,
    verify: bool | ssl.SSLContext = True,
) -> dict | None:
    """Create a pull request.

    Args:
        instance_url: Bitbucket DC instance URL
        project_key: Project key
        repo_slug: Repository slug
        access_token: HTTP Access Token
        source_branch: Source branch name
        commit_slug: Short commit hash for PR title
        target_branch: Target branch name (defaults to repo default branch)
        verify: SSL verification setting

    Returns:
        Created PR data or None if PR already exists
    """
    api_base = f"{instance_url.rstrip('/')}/rest/api/1.0"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Get default branch if target not specified
    if target_branch is None:
        target_branch = get_default_branch(
            instance_url, project_key, repo_slug, access_token, verify
        )

    pr_data = {
        "title": f"Update driver docs for commit {commit_slug}",
        "description": f"Automated update of driver documentation for commit {commit_slug}",
        "fromRef": {
            "id": f"refs/heads/{source_branch}",
            "repository": {
                "slug": repo_slug,
                "project": {"key": project_key},
            },
        },
        "toRef": {
            "id": f"refs/heads/{target_branch}",
            "repository": {
                "slug": repo_slug,
                "project": {"key": project_key},
            },
        },
    }

    url = f"{api_base}/projects/{project_key}/repos/{repo_slug}/pull-requests"

    with httpx.Client(verify=verify, timeout=30.0) as client:
        response = client.post(url, headers=headers, json=pr_data)

        try:
            response.raise_for_status()
            result = response.json()
            pr_link = result.get("links", {}).get("self", [{}])[0].get("href", "")
            print(f"Pull request created successfully: {pr_link}")
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                # PR already exists
                print("Pull request already exists for this branch")
                return None
            error_detail = ""
            try:
                error_json = e.response.json()
                error_detail = f" - {error_json}"
            except Exception:
                error_detail = f" - {e.response.text}"

            print(f"Failed to create pull request: {e}{error_detail}")
            raise


def create_pull_request_with_bot_cleanup(
    instance_url: str,
    project_key: str,
    repo_slug: str,
    access_token: str,
    branch: str,
    commit_slug: str,
    tracked_branch: str | None = None,
) -> None:
    """Create a pull request and close any existing bot PRs from docs_* branches.

    Args:
        instance_url: Bitbucket DC instance URL
        project_key: Project key
        repo_slug: Repository slug
        access_token: HTTP Access Token
        branch: Source branch name
        commit_slug: Short commit hash for PR title
        tracked_branch: Target branch (defaults to repo default branch)
    """
    BOT_NAME = "docs-bot"
    BOT_EMAIL = "bot@driverai.com"

    # Get SSL context from secrets if available
    try:
        secrets = fetch_secrets_by_installation_url(instance_url)
        verify = _get_ssl_context(secrets)
    except Exception:
        verify = True

    print("Checking for existing bot pull requests...")

    try:
        existing_prs = list_pull_requests(
            instance_url,
            project_key,
            repo_slug,
            access_token,
            state="OPEN",
            verify=verify,
        )

        for pr in existing_prs:
            source_branch = pr.get("fromRef", {}).get("displayId", "")

            if source_branch.startswith("docs_"):
                try:
                    pr_id = pr["id"]
                    commits = get_pull_request_commits(
                        instance_url,
                        project_key,
                        repo_slug,
                        pr_id,
                        access_token,
                        verify=verify,
                    )

                    # Check if any commit is authored by the bot
                    is_bot_pr = any(
                        BOT_EMAIL in commit.get("author", {}).get("emailAddress", "")
                        or BOT_NAME in commit.get("author", {}).get("name", "")
                        for commit in commits
                    )

                    if is_bot_pr:
                        try:
                            decline_pull_request(
                                instance_url,
                                project_key,
                                repo_slug,
                                pr_id,
                                access_token,
                                verify=verify,
                            )
                            print(
                                f"Closed existing bot PR #{pr_id} from branch {source_branch}"
                            )
                        except Exception as close_error:
                            print(
                                f"Warning: Could not close PR #{pr_id}: {close_error}"
                            )

                except Exception as e:
                    print(f"Error checking PR #{pr.get('id', 'unknown')}: {e}")

    except Exception as e:
        print(f"Error listing pull requests: {e}")

    # Create new pull request
    create_pull_request(
        instance_url,
        project_key,
        repo_slug,
        access_token,
        branch,
        commit_slug,
        tracked_branch,
        verify=verify,
    )


def fetch_secrets_by_installation_url(instance_url: str) -> dict:
    """Fetch secrets by matching instance URL.

    This is a fallback for when we don't have the installation_id but have the URL.
    Note: This searches through secrets which may not be efficient for large numbers
    of installations. Consider caching if this becomes a bottleneck.
    """
    # For now, return empty dict to use default SSL verification
    # In a full implementation, we'd search secrets by instance_url
    return {}
