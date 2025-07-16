import logging
import httpx
from typing import List, Tuple, Optional

from app.git_providers.utils.errors import GitProviderAccessTokenError

logger = logging.getLogger(__name__)


class BitbucketAPIResources:
    """API resources for Bitbucket using Workspace Access Tokens"""

    def __init__(self, base_url: str = None):
        self.api_base = "https://api.bitbucket.org/2.0"

    def validate_workspace_access(self, workspace: str, access_token: str) -> Tuple[bool, str]:
        """Validate WAT has access to workspace"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = f"{self.api_base}/workspaces/{workspace}"

            with httpx.Client() as client:
                response = client.get(url, headers=headers)

                if response.status_code == 200:
                    workspace_data = response.json()
                    return True, workspace_data.get("name", workspace)
                elif response.status_code == 401:
                    return False, "Invalid token or insufficient permissions"
                elif response.status_code == 404:
                    return False, f"Workspace '{workspace}' not found or no access"
                else:
                    return False, f"Unexpected error: {response.status_code}"

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def list_repositories(self, workspace: str, access_token: str) -> List[dict]:
        """List repositories in workspace using WAT"""
        headers = {"Authorization": f"Bearer {access_token}"}
        repos = []

        try:
            url = f"{self.api_base}/repositories/{workspace}"
            params = {"pagelen": 100}

            with httpx.Client() as client:
                while url:
                    response = client.get(url, headers=headers, params=params)
                    response.raise_for_status()

                    data = response.json()
                    repos.extend(data.get("values", []))

                    # Handle pagination
                    url = data.get("next")
                    params = {}  # Next URL includes params

            return repos

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed with WAT")
                raise GitProviderAccessTokenError("Invalid workspace access token")
            raise

    def get_latest_commit(self, workspace: str, repo_slug: str, access_token: str) -> str:
        """Get latest commit SHA for main branch"""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.api_base}/repositories/{workspace}/{repo_slug}/commits"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, params={"pagelen": 1})
                response.raise_for_status()

                commits = response.json().get("values", [])
                if commits:
                    return commits[0]["hash"]
                raise ValueError("No commits found")

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch commits: {e}")
            raise

    def download_repo(self, workspace: str, repo_slug: str,
                      commit: str, access_token: str) -> bytes:
        """Download repository archive using WAT"""
        headers = {"Authorization": f"Bearer {access_token}"}

        # Bitbucket download URL format
        url = f"{self.api_base}/repositories/{workspace}/{repo_slug}/downloads/{commit}.tar.gz"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers, timeout=120)
                response.raise_for_status()
                return response.content

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to download repo {workspace}/{repo_slug} at {commit}: {e}")
            raise