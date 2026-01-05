import logging
import ssl
from typing import Any

import httpx
from app.git_providers.utils.errors import GitProviderAccessTokenError

logger = logging.getLogger(__name__)


class BitbucketDCAPIResources:
    """API resources for Bitbucket Data Center/Server using HTTP Access Tokens.

    Key differences from Bitbucket Cloud:
    - API base: {instance}/rest/api/1.0 (not api.bitbucket.org/2.0)
    - Pagination: offset-based (start, limit) not cursor-based
    - Clone URL: https://:{token}@{host}/scm/{project}/{slug}.git (empty username)
    - Push event: repo:refs_changed (not repo:push)
    - PR merged event: pr:merged (not pullrequest:fulfilled)
    """

    def __init__(
        self,
        base_url: str,
        ca_bundle_path: str | None = None,
        disable_ssl_verify: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/rest/api/1.0"

        # Configure SSL context for self-signed certificates
        if disable_ssl_verify:
            self.verify: bool | ssl.SSLContext = False
        elif ca_bundle_path:
            self.verify = ssl.create_default_context()
            self.verify.load_verify_locations(ca_bundle_path)
        else:
            self.verify = True

    def get_current_user(self, access_token: str) -> dict:
        """Get current authenticated user info.

        Uses the /plugins/servlet/applinks/whoami endpoint which returns
        the username of the current authenticated user.

        Args:
            access_token: HTTP Access Token

        Returns:
            User info dictionary with at least 'name' or 'slug' field
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        # Try the application links whoami endpoint first (simpler, returns just username)
        whoami_url = f"{self.base_url}/plugins/servlet/applinks/whoami"

        try:
            with httpx.Client(verify=self.verify, timeout=30.0) as client:
                response = client.get(whoami_url, headers=headers)

                if response.status_code == 200:
                    username = response.text.strip()
                    if username:
                        return {"name": username, "slug": username}

                # Fallback to users endpoint with self-reference
                # Some versions of Bitbucket DC support /rest/api/1.0/users with no path
                users_url = f"{self.api_base}/users"
                response = client.get(
                    users_url, headers=headers, params={"filter": "", "limit": 1}
                )

                if response.status_code == 200:
                    data = response.json()
                    # The first user in the list when authenticated should be the current user
                    # But this isn't reliable, so we'll just use the first value if available
                    values = data.get("values", [])
                    if values:
                        return values[0]

                raise ValueError("Could not determine current user from token")

        except httpx.ConnectError as e:
            raise ValueError(f"Connection error: Unable to reach {self.base_url}. {e}")
        except Exception as e:
            raise ValueError(f"Failed to get current user: {e!s}")

    def validate_token(self, access_token: str) -> tuple[bool, str]:
        """Validate HTTP Access Token using Bearer auth.

        For Project/Repository tokens, we use Bearer auth only (no username needed).
        Validates by attempting to list repositories.

        Args:
            access_token: HTTP Access Token

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            # Try to list repos with limit=1 to validate the token
            url = f"{self.api_base}/repos"

            with httpx.Client(verify=self.verify, timeout=30.0) as client:
                response = client.get(url, headers=headers, params={"limit": 1})

                if response.status_code == 200:
                    return True, "Valid token"
                elif response.status_code == 401:
                    return False, "Invalid or expired token"
                elif response.status_code == 403:
                    return False, "Token does not have sufficient permissions"
                else:
                    return False, f"Unexpected error: {response.status_code}"

        except httpx.ConnectError as e:
            return False, f"Connection error: Unable to reach {self.base_url}. {e}"
        except Exception as e:
            return False, f"Validation error: {e!s}"

    def list_repositories(
        self,
        access_token: str,
        project_key: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """List accessible repositories.

        Args:
            access_token: HTTP Access Token
            project_key: Optional project key to filter by
            limit: Number of results per page (max 1000)

        Returns:
            List of repository dictionaries
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        repos = []

        try:
            if project_key:
                url = f"{self.api_base}/projects/{project_key}/repos"
            else:
                url = f"{self.api_base}/repos"

            start = 0

            with httpx.Client(verify=self.verify, timeout=60.0) as client:
                while True:
                    params = {"start": start, "limit": limit}
                    response = client.get(url, headers=headers, params=params)
                    response.raise_for_status()

                    data = response.json()
                    repos.extend(data.get("values", []))

                    # Check if this is the last page
                    if data.get("isLastPage", True):
                        break

                    # Move to next page
                    start = data.get("nextPageStart", start + limit)

            logger.info(f"Found {len(repos)} repositories")
            return repos

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed with HTTP Access Token")
                raise GitProviderAccessTokenError("Invalid HTTP access token")
            logger.error(f"HTTP error listing repositories: {e}")
            raise

    def get_repository(
        self,
        project_key: str,
        repo_slug: str,
        access_token: str,
    ) -> dict | None:
        """Get repository details.

        Args:
            project_key: Project key (typically uppercase)
            repo_slug: Repository slug
            access_token: HTTP Access Token

        Returns:
            Repository dictionary or None if not found
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.api_base}/projects/{project_key}/repos/{repo_slug}"

        try:
            with httpx.Client(verify=self.verify, timeout=30.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            if e.response.status_code == 401:
                raise GitProviderAccessTokenError("Invalid access token")
            raise

    def get_default_branch(
        self,
        project_key: str,
        repo_slug: str,
        access_token: str,
    ) -> str:
        """Get default branch for repository.

        Args:
            project_key: Project key
            repo_slug: Repository slug
            access_token: HTTP Access Token

        Returns:
            Default branch name (e.g., "main", "master")
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.api_base}/projects/{project_key}/repos/{repo_slug}/default-branch"

        try:
            with httpx.Client(verify=self.verify, timeout=30.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("displayId", "main")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"Default branch not found for {project_key}/{repo_slug}, falling back to 'main'"
                )
                return "main"
            raise

    def get_commit(
        self,
        project_key: str,
        repo_slug: str,
        commit_id: str,
        access_token: str,
    ) -> dict:
        """Get commit details.

        Args:
            project_key: Project key
            repo_slug: Repository slug
            commit_id: Commit SHA
            access_token: HTTP Access Token

        Returns:
            Commit dictionary with id, message, author info, timestamp
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.api_base}/projects/{project_key}/repos/{repo_slug}/commits/{commit_id}"

        try:
            with httpx.Client(verify=self.verify, timeout=30.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get commit {commit_id}: {e}")
            raise

    def list_branches(
        self,
        project_key: str,
        repo_slug: str,
        access_token: str,
        filter_text: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """List branches for repository.

        Args:
            project_key: Project key
            repo_slug: Repository slug
            access_token: HTTP Access Token
            filter_text: Optional filter for branch names
            limit: Results per page

        Returns:
            List of branch dictionaries
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.api_base}/projects/{project_key}/repos/{repo_slug}/branches"
        branches = []

        try:
            start = 0

            with httpx.Client(verify=self.verify, timeout=30.0) as client:
                while True:
                    params: dict[str, Any] = {"start": start, "limit": limit}
                    if filter_text:
                        params["filterText"] = filter_text

                    response = client.get(url, headers=headers, params=params)
                    response.raise_for_status()

                    data = response.json()
                    branches.extend(data.get("values", []))

                    if data.get("isLastPage", True):
                        break

                    start = data.get("nextPageStart", start + limit)

            return branches

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list branches: {e}")
            raise

    def create_repository_webhook(
        self,
        project_key: str,
        repo_slug: str,
        config: dict[str, Any],
        access_token: str,
    ) -> dict[str, Any]:
        """Create a repository-level webhook.

        Args:
            project_key: Project key
            repo_slug: Repository slug
            config: Webhook configuration with url, events, secret, etc.
            access_token: HTTP Access Token

        Returns:
            Created webhook data
        """
        url = f"{self.api_base}/projects/{project_key}/repos/{repo_slug}/webhooks"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "name": config.get("description", "Driver AI Webhook"),
            "url": config["url"],
            "active": config.get("active", True),
            "events": config["events"],
            "configuration": {},
        }

        # Add secret if provided
        if config.get("secret"):
            payload["configuration"]["secret"] = config["secret"]

        try:
            with httpx.Client(verify=self.verify, timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to create webhook: {e.response.status_code} - {e.response.text}"
            )
            raise

    def build_clone_url(
        self,
        project_key: str,
        repo_slug: str,
    ) -> str:
        """Build clone URL for Bitbucket Data Center (without embedded credentials).

        For Bitbucket DC HTTP Access Tokens (Project/Repository tokens), credentials
        must be passed via git header, not embedded in URL.

        Args:
            project_key: Project key
            repo_slug: Repository slug

        Returns:
            Clone URL in format: https://{host}/scm/{project}/{slug}.git

        Note: Token is passed via: git clone -c http.extraHeader='Authorization: Bearer TOKEN'
        """
        from urllib.parse import urlparse

        parsed = urlparse(self.base_url)
        host = parsed.netloc
        scheme = parsed.scheme

        return f"{scheme}://{host}/scm/{project_key}/{repo_slug}.git"
