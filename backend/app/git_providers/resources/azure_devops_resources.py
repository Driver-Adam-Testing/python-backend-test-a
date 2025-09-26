import base64
import logging
from typing import Any

import httpx
from database.models import GitProviderKind

logger = logging.getLogger(__name__)


class AzureDevOpsAPIResources:
    def __init__(self, base_url: str, provider_kind: GitProviderKind) -> None:
        self.base_url = base_url.rstrip("/")
        self.provider_kind = provider_kind
        self.api_version = "7.2-preview"  # Current Azure DevOps API version

    def _get_headers(self, token: str) -> dict[str, str]:
        # Azure DevOps uses Basic authentication with PAT
        credentials = f":{token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def validate_token(self, token: str) -> dict[str, Any]:
        try:
            headers = self._get_headers(token)

            url = (
                f"{self.base_url}/_apis/projects?api-version={self.api_version}&$top=1"
            )

            with httpx.Client(follow_redirects=True) as client:
                response = client.get(url, headers=headers, timeout=30.0)

                if response.status_code in [200, 203]:
                    return {"status": "success", "data": response.json()}
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

    def fetch_repositories(self, token: str, project: str) -> list[dict[str, Any]]:
        try:
            headers = self._get_headers(token)
            url = f"{self.base_url}/{project}/_apis/git/repositories?api-version={self.api_version}"

            with httpx.Client() as client:
                response = client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()

                data = response.json()
                repositories = data.get("value", [])
                return repositories
        except Exception as e:
            logger.error(f"Failed to fetch repositories for {project}: {e}")
            return []
