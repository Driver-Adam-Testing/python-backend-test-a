import base64
import logging
import re
import time
from typing import Any

import httpx
import jwt
import requests
from sqlmodel import Session

from app.core.config import settings
from app.repositories.github_app_installations_repository import (
    GithubAppInstallationsRepository,
)
from app.utils.aws_s3 import (
    generate_get_presigned_url,
    generate_put_presigned_url,
    org_id_to_hash,
)

logger = logging.getLogger(__name__)


def exchange_code_for_token(code: str) -> dict:
    url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": settings.GH_CLIENT_ID,
        "client_secret": settings.GH_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GH_REDIRECT_URI,
    }
    headers = {"Accept": "application/json"}

    with httpx.Client() as client:
        response = client.post(url, data=payload, headers=headers)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses

        token_data = response.json()
        if "access_token" not in token_data:
            raise Exception("GitHub access token not found.")

        return token_data


def is_token_valid(token: str) -> bool:
    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        return response.status_code == 200


def refresh_access_token(refresh_token: str) -> any:
    url = "https://github.com/login/oauth/access_token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.GH_CLIENT_ID,
        "client_secret": settings.GH_CLIENT_SECRET,
    }
    headers = {"Accept": "application/json"}
    with httpx.Client() as client:
        response = client.post(url, data=data, headers=headers)
        return response.json()  # This should contain the new 'access_token' and optionally a new 'refresh_token'


def generate_jwt() -> str:
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "iss": settings.GH_CLIENT_ID,
    }
    decoded_pem = base64.b64decode(settings.GH_CLIENT_PEM_SECRET)
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


def verify_app_installation_access(
    session: Session, organization_id: str, installation_id: str
) -> bool:
    """Checks that a given organization + installation ID exists. Added as a separate function to accommodate upcoming RBAC checks (if user is an admin, for instance) that have been discussed."""
    gh_repository = GithubAppInstallationsRepository(session)
    return gh_repository.exists(organization_id, installation_id)


def fetch_repos(session: Session, organization_id: str) -> list[dict[str, Any]]:
    per_page = 100
    max_pages = 100

    gh_repository = GithubAppInstallationsRepository(session)
    github_installations = gh_repository.list_by_organization_id(organization_id)

    results = []
    try:
        with httpx.Client() as client:
            for github_installation in github_installations:
                url = f"https://api.github.com/installation/repositories?per_page={per_page}"
                try:
                    token = fetch_app_access_token(
                        github_installation.github_app_installation_id
                    )
                except httpx.HTTPStatusError as ex:
                    # 404s occur when fetching an access ID for an installation
                    # if that installation is uninstalled in Github but not our DB.
                    # Assume this was the case and continue.
                    if ex.response.status_code == 404:
                        continue
                    logger.error(ex)
                    raise ex
                headers = {"Authorization": f"token {token}"}
                page_count = 1
                response = client.get(url, headers=headers)
                for repo in response.json()["repositories"]:
                    results.append(repo)
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
                        url, rel = match.groups()
                        if rel == "next" and url:
                            has_next = True
                            response = client.get(url, headers=headers)
                            response.raise_for_status()
                            results = results + response.json()["repositories"]

                    if not has_next:
                        logger.debug("Does not have next url in link header, stopping.")
                        break

                for result in results:
                    result["installation_id"] = (
                        github_installation.github_app_installation_id
                    )
        return results
    except Exception as e:
        logger.error(f"Failed to fetch repositories: {e}")
        raise e


def get_github_repo_url(org_name: str, repo: str) -> str:
    return f"https://api.github.com/repos/{org_name}/{repo}"


def fetch_default_branch_and_commit(org_name: str, repo: str, access_token: str) -> str:
    headers = {"Authorization": f"token {access_token}"}
    repo_url = get_github_repo_url(org_name, repo)

    repo_data = requests.get(repo_url, headers=headers).json()
    default_branch = repo_data["default_branch"]

    branch_url = f"{repo_url}/branches/{default_branch}"
    branch_response = requests.get(branch_url, headers=headers)
    branch_data = branch_response.json()
    logger.info(f"Default branch for {repo} in {org_name} is {default_branch}")
    logger.info(
        f"Branch data retrieved from github API (status code {branch_response.status_code}): {branch_data}"
    )
    return branch_data["commit"]["sha"]


def generate_codebase_metadata(
    org_id: str,
    org_name: str,
    workspace_id: str,
    repo: str,
    repo_id: str,
    owner: str,
    provider: str,
    commit: str,
    upload_key: str,
) -> dict:
    org_id_hash = org_id_to_hash(org_id)

    return {
        "organization_id": org_id_hash,
        "org_bucket": org_id_hash,
        "org_name": org_name,
        "workspace_id": workspace_id,
        "creator_id": owner,
        "file_path": upload_key,
        "codebase_name": repo,
        "content_type": "codebase",
        "provider": provider,
        "version": commit,
        "repository_id": repo_id,
    }


def download_github_repo_zip(
    org_name: str, repo: str, commit: str, access_token: str
) -> bytes:
    headers = {"Authorization": f"token {access_token}"}
    zip_url = f"https://api.github.com/repos/{org_name}/{repo}/zipball/{commit}"
    response = requests.get(zip_url, headers=headers, timeout=120, allow_redirects=True)
    response.raise_for_status()
    return response.content


def upload_to_s3(zip_content: bytes, metadata: dict, upload_key: str) -> bool:
    s3_url = generate_put_presigned_url(
        key=upload_key,
        content_type="application/zip",
        metadata=metadata,
    )
    if not s3_url:
        logger.error("Failed to generate S3 pre-signed URL.")
        return False

    headers = {
        "Content-Type": "application/zip",
        "Content-Length": str(len(zip_content)),
    }
    response = requests.put(s3_url, data=zip_content, headers=headers, timeout=120)
    response.raise_for_status()
    return response.status_code == 200


def download_and_upload_repo(
    gh_org_name: str,
    owner: str,
    org_id: str,
    workspace_id: str,
    repo: str,
    repo_id: str,
    access_token: str,
    upload_key: str,
    commit: str | None = None,
) -> tuple[bool, str]:
    # For parity with prior implementation, I return False on any error
    # I'm not sure why this is done; it feels like we should raise an exception
    try:
        if not commit:
            commit = fetch_default_branch_and_commit(gh_org_name, repo, access_token)

        metadata = generate_codebase_metadata(
            org_id,
            gh_org_name,
            workspace_id,
            repo,
            repo_id,
            owner,
            "github",
            commit,
            upload_key,
        )

        zip_content = download_github_repo_zip(gh_org_name, repo, commit, access_token)
        logger.info(
            "Repository downloaded successfully. Size: %d bytes", len(zip_content)
        )

        success = upload_to_s3(zip_content, metadata, upload_key)
        analysis_download_url = generate_get_presigned_url(
            key=upload_key
        )  # This is the URL that will be used to download the codebase in modal for analysis
        if success:
            logger.info("Repository %s uploaded successfully to %s.", repo, upload_key)

        return success, analysis_download_url
    except Exception:
        logger.exception("Unexpected error downloading/uploading repo.")

    return False, ""
