import base64
import hashlib
import logging
import re
import time
from typing import Any

import httpx
import jwt
from sqlmodel import Session

from app.core.config import settings
from app.repositories.github_app_installations_repository import (
    GithubAppInstallationsRepository,
)
from app.utils.aws_s3 import generate_put_presigned_url

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
                    repo["installation_id"] = (
                        github_installation.github_app_installation_id
                    )
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
        return results
    except Exception as e:
        logger.error(f"Failed to fetch repositories: {e}")
        raise e


def download_and_upload_repo(
    org_name: str,
    owner: str,
    org_id: str,
    workspace_id: str,
    repo: str,
    access_token: str,
    provider: str = "github",
) -> bool:
    github_url = f"https://api.github.com/repos/{org_name}/{repo}/zipball"
    org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    upload_key = f"codebases/{org_id_hash}/{repo}.zip"

    codebase_metadata = {
        "organization_id": org_id_hash,
        "org_bucket": org_id_hash,
        "org_name": org_name,
        "workspace_id": workspace_id,
        "creator_id": owner,
        "file_path": upload_key,
        "codebase_name": repo,
        "content_type": "codebase",
        "provider": provider,
    }
    try:
        s3_url = generate_put_presigned_url(
            key=upload_key, content_type="application/zip", metadata=codebase_metadata
        )
        print(s3_url)
        with httpx.Client(follow_redirects=True, timeout=None) as client:
            # Download repository ZIP from GitHub
            response = client.get(
                github_url,
                headers={"Authorization": f"token {access_token}"},
                timeout=None,
            )
            logger.info(response.status_code)
            response.raise_for_status()
            # print(str(len(response.content)))
            # Upload the ZIP to S3 using the pre-signed URL
            upload_response = client.put(
                s3_url,
                content=response.content,
                headers={
                    "Content-Type": "application/zip",
                    "Content-Length": str(len(response.content)),
                },
            )
            upload_response.raise_for_status()
            print(f"Repository {repo} uploaded successfully to {upload_key}.")
            return upload_response.status_code == 200
    except httpx.RequestError as e:
        print(e)
        print(f"Failed to download repository: {e}")
    except Exception as e:
        print(e)
        print(f"Failed to upload repository: {e}")

    return False
