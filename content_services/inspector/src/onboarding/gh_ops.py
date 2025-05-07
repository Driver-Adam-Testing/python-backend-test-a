import base64
import hashlib
import logging
import os
import time
from uuid import UUID

import httpx
import jwt
import requests
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
    from onboard_utils import AccessTokenError

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


def generate_codebase_metadata(
    org_id: str,
    full_repo_name: str,
    repo_id: str | int,
    provider: str,
    version_id: str | UUID,
    asset_name: str,
    install_id: str,
) -> dict:
    from database.models_v2_enums import PrimaryAssetKind

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
    from database.models_v2 import (
        PrimaryAsset,
        Version,
    )
    from database.models_v2_enums import (
        PrimaryAssetKind,
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
                        display_name=commit,
                        status=VersionStatus.CONNECTING,
                        previous_version_id=primary_asset.versions[
                            0
                        ].id,  # TODO: don't link this for connected only?
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
                                display_name=commit,
                                status=VersionStatus.GENERATING,  # Immediately jump to generating. This signals run_codebase_connection to start inspection after connection
                                previous_version_id=version.id,
                            )
                            session.add(new_version)
                            version_id = new_version.id
                            break
                        elif version.status == VersionStatus.GENERATING:
                            print(
                                f"Version already in generating state for {repo["name"]}, skipping..."
                            )
                            return repo
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
