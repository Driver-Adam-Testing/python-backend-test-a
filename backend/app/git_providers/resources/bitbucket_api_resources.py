import logging
from collections.abc import Callable
from typing import Any

import httpx
from app.git_providers.utils.errors import GitProviderAccessTokenError
from app.git_providers.utils.rate_limiter import (
    BitbucketRateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
)

logger = logging.getLogger(__name__)


class BitbucketAPIResources:
    """API resources for Bitbucket using Workspace Access Tokens with rate limiting"""

    def __init__(self, rate_limit_config: RateLimitConfig | None = None) -> None:
        self.api_base = "https://api.bitbucket.org/2.0"

        # Initialize rate limiter with custom config or defaults
        if rate_limit_config is None:
            rate_limit_config = RateLimitConfig(
                max_requests_per_hour=1000,  # Default for authenticated requests
                max_retries=5,
                initial_delay=1.0,
                max_delay=60.0,
                backoff_factor=2.0,
                strategy=RateLimitStrategy.EXPONENTIAL_BACKOFF,
                respect_retry_after=True,
                min_request_interval=0.5,  # 500ms between requests to be safe
            )
        self.rate_limiter = BitbucketRateLimiter(rate_limit_config)

    def validate_workspace_access(
        self, workspace: str, access_token: str
    ) -> tuple[bool, str]:
        """Validate Workspace Access Token by checking actual permissions with rate limiting"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            repos_url = f"{self.api_base}/repositories/{workspace}"

            def make_request():
                with httpx.Client() as client:
                    return client.get(repos_url, headers=headers, params={"pagelen": 1})

            # Execute with rate limiting, using the token as the rate limit key
            repos_response = self.rate_limiter.execute_with_retry(
                make_request,
                key=f"token_{access_token[:8]}",  # Use first 8 chars of token as key
                extract_headers=lambda resp: dict(resp.headers),
            )

            if repos_response.status_code == 200:
                return True, f"Valid workspace access token for {workspace}"
            elif repos_response.status_code == 403:
                return (
                    False,
                    f"Token does not have access to workspace '{workspace}'",
                )
            elif repos_response.status_code == 401:
                return False, "Invalid token"
            elif repos_response.status_code == 404:
                return False, f"Workspace '{workspace}' not found or no access"
            else:
                return False, f"Unexpected error: {repos_response.status_code}"

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return False, "Rate limit exceeded. Please try again later."
            return False, f"HTTP error: {e}"
        except Exception as e:
            return False, f"Connection error: {e!s}"

    def fetch_repositories_page(
        self,
        workspace: str,
        access_token: str,
        page_size: int = 100,
        page_url: str | None = None,
        params: dict | None = None,
    ) -> dict:
        """
        Fetch a single page of repositories with rate limiting.

        Args:
            workspace: Bitbucket workspace name
            access_token: Access token for authentication
            page_size: Number of items per page (default: 100)
            page_url: Specific page URL to fetch (for pagination)
            params: Additional query parameters

        Returns:
            Dictionary with 'values' (repositories) and 'next' (next page URL)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        rate_limit_key = f"token_{access_token[:8]}"

        # Use provided URL or construct initial URL
        url = page_url or f"{self.api_base}/repositories/{workspace}"

        # Only add params if not using a page_url (which includes params)
        if not page_url and params is None:
            params = {"pagelen": page_size}
        elif not page_url:
            params = {**params, "pagelen": page_size}
        else:
            params = {}  # page_url already includes params

        try:

            def make_request():
                with httpx.Client(timeout=30.0) as client:
                    return client.get(url, headers=headers, params=params)

            response = self.rate_limiter.execute_with_retry(
                make_request,
                key=rate_limit_key,
                extract_headers=lambda resp: dict(resp.headers),
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed with access token")
                raise GitProviderAccessTokenError("Invalid access token")
            elif e.response.status_code == 429:
                logger.error(
                    f"Rate limit exceeded while fetching repositories from {workspace}"
                )
                raise GitProviderAccessTokenError(
                    "Rate limit exceeded. Please wait a few minutes and try again."
                )
            raise
        except Exception as e:
            logger.error(f"Error fetching repository page from {workspace}: {e}")
            raise

    def list_repositories(
        self,
        workspace: str,
        access_token: str,
        page_size: int = 100,
        max_pages: int | None = None,
        auto_paginate: bool = True,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[dict]:
        """
        List repositories with flexible pagination control.

        Args:
            workspace: Bitbucket workspace name
            access_token: Access token for authentication
            page_size: Number of items per page (default: 100, max: 100)
            max_pages: Maximum number of pages to fetch (None = no limit)
            auto_paginate: If True, automatically fetch all pages (default: True)
            progress_callback: Optional callback(repos_fetched, page_count) for progress updates

        Returns:
            List of repository dictionaries
        """
        if not auto_paginate:
            # Return just the first page if auto_paginate is False
            data = self.fetch_repositories_page(workspace, access_token, page_size)
            return data.get("values", [])

        repos = []
        page_count = 0
        url = None

        # Set a reasonable default max_pages if not specified
        if max_pages is None:
            max_pages = 1000  # Very high limit as safety measure

        try:
            while page_count < max_pages:
                # Fetch page
                data = self.fetch_repositories_page(
                    workspace, access_token, page_size, page_url=url
                )

                # Extract repositories
                page_repos = data.get("values", [])
                if not page_repos:
                    break  # No more data

                repos.extend(page_repos)
                page_count += 1

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(len(repos), page_count)

                # Log progress periodically
                if page_count % 5 == 0:
                    logger.info(
                        f"Fetched {len(repos)} repositories from {workspace} (page {page_count})"
                    )

                # Check for next page
                url = data.get("next")
                if not url:
                    break  # No more pages

                # Optional delay between pages to be respectful
                # Only if we're fetching multiple pages
                if url and page_count > 1:
                    import time

                    time.sleep(0.05)  # 50ms delay between pages

            logger.info(
                f"Successfully fetched {len(repos)} repositories from {workspace} in {page_count} pages"
            )
            return repos

        except Exception as e:
            logger.error(f"Error during pagination: {e}")
            raise

    def list_project_repositories(
        self,
        workspace: str,
        project_key: str,
        access_token: str,
        page_size: int = 100,
        max_pages: int | None = None,
        auto_paginate: bool = True,
    ) -> list[dict]:
        """
        List project repositories with flexible pagination control.

        Args:
            workspace: Bitbucket workspace name
            project_key: Project key to filter repositories
            access_token: Access token for authentication
            page_size: Number of items per page (default: 100)
            max_pages: Maximum number of pages to fetch (None = no limit)
            auto_paginate: If True, automatically fetch all pages (default: True)

        Returns:
            List of repository dictionaries for the specified project
        """
        # Use the base list_repositories with project filter
        base_params = {"q": f'project.key="{project_key}"'}

        if not auto_paginate:
            data = self.fetch_repositories_page(
                workspace, access_token, page_size, params=base_params
            )
            repos = data.get("values", [])
            logger.info(
                f"Found {len(repos)} repositories in project {project_key} (first page)"
            )
            return repos

        # For auto-pagination, we need to handle it ourselves due to the query parameter
        repos = []
        page_count = 0
        url = None
        max_pages = max_pages or 1000

        try:
            while page_count < max_pages:
                # Fetch page with project filter
                data = self.fetch_repositories_page(
                    workspace,
                    access_token,
                    page_size,
                    page_url=url,
                    params=base_params
                    if not url
                    else None,  # Only add params on first request
                )

                # Extract repositories
                page_repos = data.get("values", [])
                if not page_repos:
                    break

                repos.extend(page_repos)
                page_count += 1

                # Check for next page
                url = data.get("next")
                if not url:
                    break

                # Small delay between pages
                if url and page_count > 1:
                    import time

                    time.sleep(0.05)

            logger.info(
                f"Found {len(repos)} repositories in project {project_key} ({page_count} pages)"
            )
            return repos

        except Exception as e:
            logger.error(f"Error fetching project repositories: {e}")
            raise

    def get_default_branch(self, workspace: str, repo_slug: str) -> str:
        pass

    def get_repository(
        self, workspace: str, repo_slug: str, access_token: str
    ) -> dict | None:
        """Get repository details with rate limiting"""
        headers = {"Authorization": f"Bearer {access_token}"}
        rate_limit_key = f"token_{access_token[:8]}"

        try:
            url = f"{self.api_base}/repositories/{workspace}/{repo_slug}"

            def make_request():
                with httpx.Client() as client:
                    return client.get(url, headers=headers)

            response = self.rate_limiter.execute_with_retry(
                make_request,
                key=rate_limit_key,
                extract_headers=lambda resp: dict(resp.headers),
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            if e.response.status_code == 401:
                raise GitProviderAccessTokenError("Invalid access token")
            if e.response.status_code == 429:
                logger.warning(f"Rate limit hit when fetching repository {repo_slug}")
                return None  # Return None instead of raising for single repo fetches
            raise

    def get_latest_commit(
        self, workspace: str, repo_slug: str, access_token: str
    ) -> str:
        """Get latest commit SHA for default branch"""

        # TODO prior implementation was wrong in that default branch was not specified
        # this codepath is unused right now so the impl is empty :) use git blame

    def download_repo(
        self, workspace: str, repo_slug: str, commit: str, access_token: str
    ) -> bytes:
        """Download repository using git clone with WAT"""
        import shutil
        import subprocess
        import tempfile
        import zipfile
        from pathlib import Path

        logger.info(
            f"Using git clone to download repository {workspace}/{repo_slug} at commit {commit}"
        )

        # Create a temporary directory for cloning
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / repo_slug

            # Clone URL with x-token-auth and the access token
            clone_url = f"https://x-token-auth:{access_token}@bitbucket.org/{workspace}/{repo_slug}.git"

            try:
                # Clone the repository
                logger.info("Cloning repository...")
                clone_cmd = [
                    "git",
                    "clone",
                    "--no-checkout",  # Don't checkout files yet
                    clone_url,
                    str(repo_path),
                ]

                clone_result = subprocess.run(
                    clone_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                if clone_result.returncode != 0:
                    logger.error(f"Clone failed: {clone_result.stderr}")
                    raise Exception(
                        f"Failed to clone repository: {clone_result.stderr}"
                    )

                logger.info(
                    "Repository cloned successfully, checking out specific commit..."
                )

                # Checkout the specific commit
                checkout_result = subprocess.run(
                    ["git", "checkout", commit],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                )

                if checkout_result.returncode != 0:
                    logger.warning(
                        f"Could not checkout commit {commit}: {checkout_result.stderr}"
                    )
                    # Try fetching all commits
                    logger.info("Fetching all commits and trying again...")

                    subprocess.run(
                        ["git", "fetch", "--unshallow"],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                    )

                    # Try checkout again
                    checkout_result = subprocess.run(
                        ["git", "checkout", commit],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                    )

                    if checkout_result.returncode != 0:
                        logger.error(
                            f"Failed to checkout commit {commit}: {checkout_result.stderr}"
                        )
                        raise Exception(f"Failed to checkout commit {commit}")

                logger.info(f"Successfully checked out commit {commit}")

                # Remove .git directory to reduce size
                git_dir = repo_path / ".git"
                if git_dir.exists():
                    shutil.rmtree(git_dir)

                # Create a zip archive
                zip_path = Path(temp_dir) / f"{repo_slug}.zip"
                logger.info("Creating zip archive...")

                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    # Walk through all files and add them to the zip
                    for file_path in repo_path.rglob("*"):
                        if file_path.is_file():
                            # Get the relative path from the repo root
                            arcname = file_path.relative_to(repo_path)
                            zipf.write(file_path, arcname)

                # Read the zip file content
                with open(zip_path, "rb") as f:
                    zip_content = f.read()

                logger.info(
                    f"Archive created successfully. Size: {len(zip_content)} bytes"
                )
                return zip_content

            except subprocess.TimeoutExpired:
                raise Exception("Git clone operation timed out")
            except Exception as e:
                logger.error(f"Error during repository download: {e!s}")
                raise

    def create_workspace_webhook(
        self, workspace: str, config: dict[str, Any], access_token: str
    ) -> dict[str, Any]:
        """Create a workspace-level webhook with rate limiting"""
        url = f"{self.api_base}/workspaces/{workspace}/hooks"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        rate_limit_key = f"token_{access_token[:8]}"

        payload = {
            "description": config["description"],
            "url": config["url"],
            "active": config["active"],
            "events": config["events"],
        }

        # Only add secret if provided
        if config.get("secret"):
            payload["secret"] = config["secret"]

        try:

            def make_request():
                with httpx.Client() as client:
                    return client.post(url, headers=headers, json=payload)

            response = self.rate_limiter.execute_with_retry(
                make_request,
                key=rate_limit_key,
                extract_headers=lambda resp: dict(resp.headers),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("Rate limit exceeded when creating webhook")
                raise GitProviderAccessTokenError(
                    "Rate limit exceeded. Please wait and try again."
                )
            logger.error(
                f"Failed to create workspace webhook: {e.response.status_code} - {e.response.text}"
            )
            raise

    def create_repository_webhook(
        self, workspace: str, repo_slug: str, config: dict[str, Any], access_token: str
    ) -> dict[str, Any]:
        """Create a repository-level webhook with rate limiting"""
        url = f"{self.api_base}/repositories/{workspace}/{repo_slug}/hooks"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        rate_limit_key = f"token_{access_token[:8]}"

        payload = {
            "description": config["description"],
            "url": config["url"],
            "active": config["active"],
            "events": config["events"],
        }

        # Only add secret if provided
        if config.get("secret"):
            payload["secret"] = config["secret"]

        try:

            def make_request():
                with httpx.Client() as client:
                    return client.post(url, headers=headers, json=payload)

            response = self.rate_limiter.execute_with_retry(
                make_request,
                key=rate_limit_key,
                extract_headers=lambda resp: dict(resp.headers),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("Rate limit exceeded when creating webhook")
                raise GitProviderAccessTokenError(
                    "Rate limit exceeded. Please wait and try again."
                )
            logger.error(
                f"Failed to create repository webhook: {e.response.status_code} - {e.response.text}"
            )
            raise
