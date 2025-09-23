import base64
import logging
from typing import Any

import httpx
from database.models import GitProviderKind

logger = logging.getLogger(__name__)


class AzureDevOpsAPIResources:
    """Azure DevOps API resource management"""

    def __init__(self, base_url: str, provider_kind: GitProviderKind) -> None:
        self.base_url = base_url.rstrip("/")
        self.provider_kind = provider_kind
        self.api_version = "7.2-preview"  # Current Azure DevOps API version

    def _get_headers(self, token: str) -> dict[str, str]:
        """Get headers for Azure DevOps API requests"""
        # Azure DevOps uses Basic authentication with PAT
        credentials = f":{token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def validate_token(self, token: str) -> dict[str, Any]:
        """Validate Personal Access Token against Azure DevOps API"""
        try:
            headers = self._get_headers(token)

            # Try organization-specific endpoint first, fall back to global if no org
            url = (
                f"{self.base_url}/_apis/projects?api-version={self.api_version}&$top=1"
            )

            with httpx.Client(follow_redirects=True) as client:
                response = client.get(url, headers=headers, timeout=30.0)

                if response.status_code in [200, 203]:
                    return {"status": "success", "data": response.json()}
                elif response.status_code == 302:
                    # Handle redirect - try to follow it or use alternative endpoint
                    redirect_url = response.headers.get("location")
                    if redirect_url:
                        logger.info(f"Following redirect to: {redirect_url}")
                        redirect_response = client.get(
                            redirect_url, headers=headers, timeout=30.0
                        )
                        if redirect_response.status_code == 200:
                            return {
                                "status": "success",
                                "data": redirect_response.json(),
                            }
                        else:
                            return {
                                "status": "error",
                                "error": f"Redirect validation failed with status {redirect_response.status_code}",
                            }
                    else:
                        return {
                            "status": "error",
                            "error": "Received redirect but no location header",
                        }
                elif response.status_code == 401:
                    return {"status": "error", "error": "Invalid Personal Access Token"}
                elif response.status_code == 403:
                    return {
                        "status": "error",
                        "error": "Personal Access Token lacks required permissions",
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"Token validation failed with status {response.status_code}",
                    }
        except httpx.TimeoutException:
            return {"status": "error", "error": "Request timeout"}
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return {"status": "error", "error": str(e)}

    def fetch_organizations(self, token: str) -> list[dict[str, Any]]:
        """Fetch accessible organizations"""
        try:
            headers = self._get_headers(token)
            # Use Visual Studio Team Services API for account discovery
            url = f"https://app.vssps.visualstudio.com/_apis/accounts?api-version={self.api_version}&memberId=me"

            with httpx.Client() as client:
                response = client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()

                data = response.json()
                return data.get("value", [])
        except Exception as e:
            logger.error(f"Failed to fetch organizations: {e}")
            return []

    def fetch_projects(self, token: str, organization: str) -> list[dict[str, Any]]:
        """Fetch projects in an organization"""
        try:
            headers = self._get_headers(token)
            url = f"{self.base_url}/{organization}/_apis/projects?api-version={self.api_version}"

            with httpx.Client() as client:
                response = client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()

                data = response.json()
                return data.get("value", [])
        except Exception as e:
            logger.error(
                f"Failed to fetch projects for organization {organization}: {e}"
            )
            return []

    def fetch_repositories(self, token: str, project: str) -> list[dict[str, Any]]:
        """Fetch repositories in a project"""
        try:
            headers = self._get_headers(token)
            url = f"{self.base_url}/{project}/_apis/git/repositories?api-version={self.api_version}"

            with httpx.Client() as client:
                response = client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()

                data = response.json()
                repositories = data.get("value", [])

                # Enrich repository data with additional information
                enriched_repos = []
                for repo in repositories:
                    enriched_repo = self._enrich_repository_data(token, project, repo)
                    enriched_repos.append(enriched_repo)

                return enriched_repos
        except Exception as e:
            logger.error(f"Failed to fetch repositories for {project}: {e}")
            return []

    def _enrich_repository_data(
        self, token: str, project: str, repo: dict[str, Any]
    ) -> dict[str, Any]:
        """Enrich repository data with additional information"""
        try:
            headers = self._get_headers(token)
            repo_id = repo["id"]

            # Get default branch information
            refs_url = f"{self.base_url}/{project}/_apis/git/repositories/{repo_id}/refs?api-version={self.api_version}"

            with httpx.Client() as client:
                response = client.get(refs_url, headers=headers, timeout=30.0)
                if response.status_code == 200:
                    refs_data = response.json()
                    refs = refs_data.get("value", [])

                    # Find default branch
                    default_branch = None
                    for ref in refs:
                        if ref.get("name", "").startswith("refs/heads/"):
                            branch_name = ref["name"].replace("refs/heads/", "")
                            if branch_name == repo.get("defaultBranch", "").replace(
                                "refs/heads/", ""
                            ):
                                default_branch = branch_name
                                break

                    repo["default_branch"] = default_branch or "main"
                else:
                    repo["default_branch"] = "main"

            return repo
        except Exception as e:
            logger.error(
                f"Failed to enrich repository data for {repo.get('name', 'unknown')}: {e}"
            )
            return repo

    def download_repository_archive(
        self,
        token: str,
        organization: str,
        project: str,
        repository_id: str,
        ref: str = "main",
    ) -> bytes | None:
        """Download repository archive as ZIP"""
        try:
            headers = self._get_headers(token)
            # Remove 'Accept' header for binary content
            headers.pop("Accept", None)

            url = f"{self.base_url}/{organization}/{project}/_apis/git/repositories/{repository_id}/items?api-version={self.api_version}&scopePath=/&download=true&$format=zip&version={ref}"

            with httpx.Client() as client:
                response = client.get(
                    url, headers=headers, timeout=300.0
                )  # 5 minute timeout for large repos
                response.raise_for_status()

                return response.content
        except Exception as e:
            logger.error(f"Failed to download repository archive: {e}")
            return None

    def get_repository_content(
        self,
        token: str,
        organization: str,
        project: str,
        repository_id: str,
        path: str = "/",
        ref: str = "main",
    ) -> dict[str, Any] | None:
        """Get repository content at a specific path"""
        try:
            headers = self._get_headers(token)
            url = f"{self.base_url}/{organization}/{project}/_apis/git/repositories/{repository_id}/items?api-version={self.api_version}&scopePath={path}&version={ref}"

            with httpx.Client() as client:
                response = client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()

                return response.json()
        except Exception as e:
            logger.error(f"Failed to get repository content: {e}")
            return None
