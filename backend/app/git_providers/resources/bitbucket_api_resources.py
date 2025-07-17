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
        """Validate Workspace Access Token by checking actual permissions"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            # Method 1: Try to list repositories in the workspace
            # This will fail with 403 if we don't have access
            repos_url = f"{self.api_base}/repositories/{workspace}"

            with httpx.Client() as client:
                repos_response = client.get(
                    repos_url,
                    headers=headers,
                    # params={"pagelen": 1}  # Just need to check access
                )

                if repos_response.status_code == 200:
                    # Can list repos = have workspace access
                    return True, f"Valid workspace access token for {workspace}"
                elif repos_response.status_code == 403:
                    return False, f"Token does not have access to workspace '{workspace}'"
                elif repos_response.status_code == 401:
                    return False, "Invalid token"
                elif repos_response.status_code == 404:
                    # Workspace doesn't exist OR we don't have access
                    # Try to determine which by checking if workspace exists publicly
                    return False, f"Workspace '{workspace}' not found or no access"
                else:
                    return False, f"Unexpected error: {repos_response.status_code}"

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def validate_project_access(self, workspace: str, project_key: str,
                                access_token: str) -> Tuple[bool, str]:
        """Validate Project Access Token"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            # Try to access the project
            url = f"{self.api_base}/workspaces/{workspace}/projects/{project_key}"

            with httpx.Client() as client:
                response = client.get(url, headers=headers)

                if response.status_code == 200:
                    return True, "Valid project access token"
                elif response.status_code == 401:
                    return False, "Invalid token or insufficient permissions"
                elif response.status_code == 404:
                    return False, f"Project '{project_key}' not found or no access"
                else:
                    return False, f"Unexpected error: {response.status_code}"

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def validate_repository_access(self, workspace: str, repo_slug: str,
                                   access_token: str) -> Tuple[bool, str]:
        """Validate Repository Access Token"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            # Try to access the specific repository
            url = f"{self.api_base}/repositories/{workspace}/{repo_slug}"

            with httpx.Client() as client:
                response = client.get(url, headers=headers)

                if response.status_code == 200:
                    return True, "Valid repository access token"
                elif response.status_code == 401:
                    return False, "Invalid token or insufficient permissions"
                elif response.status_code == 404:
                    return False, f"Repository '{repo_slug}' not found or no access"
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

    def list_project_repositories(self, workspace: str, project_key: str,
                                  access_token: str) -> List[dict]:
        """List all repositories in a project"""
        headers = {"Authorization": f"Bearer {access_token}"}
        repos = []

        try:
            # Use query parameter to filter by project
            url = f"{self.api_base}/repositories/{workspace}"
            params = {
                "pagelen": 100,
                "q": f'project.key="{project_key}"'
            }

            with httpx.Client() as client:
                while url:
                    response = client.get(url, headers=headers, params=params)
                    response.raise_for_status()

                    data = response.json()
                    repos.extend(data.get("values", []))

                    # Handle pagination
                    url = data.get("next")
                    params = {}  # Next URL includes params

            logger.info(f"Found {len(repos)} repositories in project {project_key}")
            return repos

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed with project access token")
                raise GitProviderAccessTokenError("Invalid project access token")
            raise

    def get_repository(self, workspace: str, repo_slug: str,
                       access_token: str) -> Optional[dict]:
        """Get a single repository"""
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            url = f"{self.api_base}/repositories/{workspace}/{repo_slug}"

            with httpx.Client() as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            if e.response.status_code == 401:
                raise GitProviderAccessTokenError("Invalid access token")
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