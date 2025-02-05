import base64
import hashlib
import logging
import os
import re
import time
from typing import Any
from uuid import UUID

import boto3
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
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    jwt = generate_jwt()
    with httpx.Client() as client:
        headers = {"Accept": "application/json", "Authorization": f"Bearer {jwt}"}
        response = client.post(url, headers=headers)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses
        token_data = response.json()
        if "token" not in token_data:
            raise Exception("GitHub application access token not found.")
        return token_data["token"]


def fetch_repos(installation_id: str) -> list[dict[str, Any]]:
    per_page = 100
    max_pages = 100

    all_results = []
    try:
        with httpx.Client() as client:
            url = (
                f"https://api.github.com/installation/repositories?per_page={per_page}"
            )
            try:
                token = fetch_app_access_token(
                    installation_id=installation_id,
                )
            except httpx.HTTPStatusError as ex:
                # 404s occur when fetching an access ID for an installation
                # if that installation is uninstalled in Github but not our DB.
                # Assume this was the case and continue.
                if ex.response.status_code == 404:
                    print("Github installation not found. Assuming uninstalled.")
                    raise ex
            headers = {"Authorization": f"token {token}"}
            page_count = 1
            response = client.get(url, headers=headers)
            response.raise_for_status()
            current_repos = response.json()["repositories"]
            for repo in current_repos:
                repo["installation_id"] = installation_id
            all_results.extend(current_repos)
            link_header: str = response.headers.get("link", None)
            while link_header:
                page_count = page_count + 1
                if page_count > max_pages:
                    # GH API has rate limits that will probably kick in before we get this far.
                    # Protecting ourselves from infinite loops explicitly too.
                    # We should implement exponential backoff and parse the
                    # rate limit responses being returned by GH here.
                    raise ValueError("Aborting GH API pagination at 10000 results.")
                parts = response.headers["link"].split(",")
                matches = [
                    re.search(r'<([^>]+)>; rel="([^"]+)"', part.strip())
                    for part in parts
                ]
                has_next = False
                for match in matches:
                    next_url, rel = match.groups()
                    if rel == "next" and next_url:
                        has_next = True
                        response = client.get(next_url, headers=headers)
                        response.raise_for_status()
                        current_repos = response.json()["repositories"]
                        for repo in current_repos:
                            repo["installation_id"] = installation_id
                        all_results.extend(current_repos)

                if not has_next:
                    break

        return all_results
    except Exception as e:
        print(f"Failed to fetch repositories: {e}")
        raise e


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
) -> dict:
    return {
        "unhashed_organization_id": org_id,
        "full_repo_name": full_repo_name,
        "provider": provider,
        "version_id": str(version_id),
        "repository_id": str(repo_id),
    }


def download_github_repo_zip(full_name: str, commit: str, access_token: str) -> bytes:
    headers = {"Authorization": f"token {access_token}"}
    zip_url = f"https://api.github.com/repos/{full_name}/zipball/{commit}"
    response = requests.get(zip_url, headers=headers, timeout=120, allow_redirects=True)
    response.raise_for_status()
    return response.content


def upload_to_s3_with_metadata(
    zip_content: bytes, metadata: dict, upload_key: str
) -> bool:
    s3_client = boto3.client("s3")
    try:
        s3_client.put_object(
            Bucket=os.environ["DROPZONE_BUCKET_NAME"],
            Key=upload_key,
            Body=zip_content,
            ContentType="application/zip",
            Metadata=metadata,
        )
    except Exception as e:
        print(e)
        raise Exception(
            f"Failed uploading codebase version {metadata['version_id']} to {upload_key}."
        ) from e


def download_and_upload_repo(
    org_id: str, repo: dict, access_token: str, is_push: bool = False
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
    from sqlalchemy.exc import IntegrityError

    if not repo.get("commit"):
        commit = fetch_default_branch_and_commit(repo["full_name"], access_token)
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

    metadata = generate_codebase_metadata(
        org_id,
        repo["full_name"],
        repo["id"],
        "github",
        version_id,
    )

    zip_content = download_github_repo_zip(repo["full_name"], commit, access_token)
    logger.info("Repository downloaded successfully. Size: %d bytes", len(zip_content))

    org_hashed_id = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    upload_key = f"codebases/{org_hashed_id}/{repo['name']}.zip"
    upload_to_s3_with_metadata(zip_content, metadata, upload_key)
    print(f"Repository {repo['name']} uploaded successfully to {upload_key}.")

    return None
