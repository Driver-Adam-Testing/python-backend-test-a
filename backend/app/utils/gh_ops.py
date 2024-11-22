import hashlib
import logging
import re
from typing import Any

import httpx
import requests

from app.core.config import settings
from app.utils.aws_s3 import generate_put_presigned_url

logger = logging.getLogger(__name__)


async def exchange_code_for_token(code: str) -> dict:
    url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": settings.GH_CLIENT_ID,
        "client_secret": settings.GH_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GH_REDIRECT_URI,
    }
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=payload, headers=headers)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses

        token_data = response.json()
        if "access_token" not in token_data:
            raise Exception("GitHub access token not found.")

        return token_data


async def is_token_valid(token: str) -> bool:
    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.status_code == 200


async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    url = "https://github.com/login/oauth/access_token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.GH_CLIENT_ID,
        "client_secret": settings.GH_CLIENT_SECRET,
    }
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers)
        return response.json()  # This should contain the new 'access_token' and optionally a new 'refresh_token'


# fetch user orgs
async def fetch_repos(token: str) -> list[dict[str, Any]]:
    per_page = 100
    max_pages = 100
    url = f"https://api.github.com/user/repos?per_page={per_page}"
    headers = {"Authorization": f"token {token}"}

    results = []
    try:
        async with httpx.AsyncClient() as client:
            page_count = 1
            response = await client.get(url, headers=headers)
            response.raise_for_status()  # Raises an exception for 4XX/5XX responses
            results = results + response.json()
            # The last page will end with rel="first". Example:
            # <https://api.github.com/user/repos?per_page=5&page=5>; rel="prev", <https://api.github.com/user/repos?per_page=5&page=1>; rel="first"
            while "link" in response.headers and response.headers.get("link").endswith(
                'rel="last"'
            ):
                page_count = page_count + 1
                if page_count > max_pages:
                    # GH API has rate limits that will probably kick in before we get this far.
                    # Protecting ourselves from infinite loops explicitly too.
                    # We should implement exponential backoff and parse the
                    # rate limit responses being returned by GH here.
                    raise ValueError("Aborting GH API pagination at 10000 pages.")
                parts = response.headers["link"].split(",")
                match = re.search(r'<([^>]+)>; rel="([^"]+)"', parts[0].strip())
                if match:
                    next_url, rel = match.groups()
                    response = await client.get(next_url, headers=headers)
                    response.raise_for_status()
                    results = results + response.json()
                else:
                    raise ValueError(
                        "Unable to parse link header for GitHub pagination"
                    )
        return results
    except Exception as e:
        print(f"Failed to fetch repositories: {e}")
        raise e


def get_github_repo_url(org_name: str, repo: str) -> str:
    return f"https://api.github.com/repos/{org_name}/{repo}"


def fetch_default_branch_and_commit(org_name: str, repo: str, access_token: str) -> str:
    headers = {"Authorization": f"token {access_token}"}
    repo_url = get_github_repo_url(org_name, repo)

    repo_data = requests.get(repo_url, headers=headers).json()
    default_branch = repo_data["default_branch"]

    branch_url = f"{repo_url}/branches/{default_branch}"
    branch_data = requests.get(branch_url, headers=headers).json()

    return branch_data["commit"]["sha"]


def generate_codebase_metadata(
    org_id: str,
    org_name: str,
    workspace_id: str,
    repo: str,
    owner: str,
    provider: str,
    commit: str,
) -> dict:
    org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    upload_key = f"codebases/{org_id_hash}/{repo}.zip"

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
    org_name: str,
    owner: str,
    org_id: str,
    workspace_id: str,
    repo: str,
    access_token: str,
    commit: str | None = None,
) -> bool:
    # For parity with prior implementation, I return False on any error
    # I'm not sure why this is done; it feels like we should raise an exception
    try:
        if not commit:
            commit = fetch_default_branch_and_commit(org_name, repo, access_token)

        metadata = generate_codebase_metadata(
            org_id, org_name, workspace_id, repo, owner, "github", commit
        )
        upload_key = metadata["file_path"]

        zip_content = download_github_repo_zip(org_name, repo, commit, access_token)
        logger.info(
            "Repository downloaded successfully. Size: %d bytes", len(zip_content)
        )

        success = upload_to_s3(zip_content, metadata, upload_key)
        if success:
            logger.info("Repository %s uploaded successfully to %s.", repo, upload_key)
        return success
    except requests.RequestException as e:
        logger.error("Request error: %s", e)
    except Exception as e:
        logger.error("Unexpected error: %s", e)

    return False
