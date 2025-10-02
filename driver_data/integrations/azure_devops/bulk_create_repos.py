#!/usr/bin/env python3
"""
Azure DevOps Bulk Repository Creator with Personal Access Token Authentication
Creates multiple repositories in an Azure DevOps project for rate limiting tests.
Updated with ability to delete all repositories in a project or list repositories.
"""

import argparse
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests


class AzureDevOpsBulkCreator:
    def __init__(
        self,
        personal_access_token: str,
        organization: str,
        project: str,
    ) -> None:
        """
        Initialize the Azure DevOps API client with Personal Access Token.

        Args:
            personal_access_token: Azure DevOps Personal Access Token
            organization: Azure DevOps organization name
            project: Project name where repos will be created
        """
        self.pat = personal_access_token
        self.organization = organization
        self.project = project
        self.project_id = None  # Will be fetched during verification
        self.base_url = f"https://dev.azure.com/{organization}"
        self.api_version = "7.2-preview"  # Azure DevOps API version
        self.session = requests.Session()

        print(f"Using organization: {self.organization}")
        print(f"Using project: {self.project}")
        print(f"Using PAT: {'*' * (len(self.pat) - 4) + self.pat[-4:]}")

        # Set up authorization header (Azure DevOps uses Basic auth with PAT)
        credentials = f":{personal_access_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update(
            {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Rate limiting tracking
        self.request_count = 0
        self.rate_limit_remaining = 60  # Azure DevOps conservative limit
        self.rate_limit_reset = None

    def verify_token(self) -> bool:
        """Verify that the Personal Access Token is valid."""
        try:
            url = (
                f"{self.base_url}/_apis/projects?api-version={self.api_version}&$top=1"
            )
            print(url)
            # Use the Azure DevOps profile API to verify the token
            response = self.session.get(url)
            print(response.status_code)
            if response.status_code in [200, 203]:
                # print(response.text)
                # user_data = response.json()
                # display_name = user_data.get("displayName", "Unknown")
                print("✓ Token verified successfully")
                return True
            else:
                print(f"✗ Token verification failed: HTTP {response.status_code}")
                if response.status_code == 401:
                    print("   Authentication failed - check your Personal Access Token")
                elif response.status_code == 403:
                    print(
                        "   Access denied - ensure your PAT has the required permissions"
                    )
                return False
        except Exception as e:
            print(e)
            print(f"✗ Token verification error: {e}")
            return False

    def verify_project(self) -> bool:
        """Verify that the project exists and is accessible."""
        try:
            response = self.session.get(
                f"{self.base_url}/_apis/projects/{self.project}?api-version={self.api_version}"
            )
            print(response.status_code)
            if response.status_code == 200:
                project_data = response.json()
                project_name = project_data.get("name", "Unknown")
                project_state = project_data.get("state", "Unknown")
                # Store the project ID for later use
                self.project_id = project_data.get("id")
                print(
                    f"✓ Project verified: {project_name} (State: {project_state}, ID: {self.project_id})"
                )
                return True
            else:
                print(f"✗ Project verification failed: HTTP {response.status_code}")
                if response.status_code == 404:
                    print(
                        f"   Project '{self.project}' not found in organization '{self.organization}'"
                    )
                return False
        except Exception as e:
            print(f"✗ Project verification error: {e}")
            return False

    def check_rate_limit(self, response: requests.Response) -> None:
        """Extract and track rate limit information from response."""
        self.request_count += 1

        # Azure DevOps rate limiting headers
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in response.headers:
            self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])

        # Azure DevOps may also use Retry-After header
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", 60)
            print(f"Rate limited! Retry after {retry_after} seconds")

        print(
            f"Request #{self.request_count} | "
            f"Rate Limit Remaining: {self.rate_limit_remaining} | "
            f"Status: {response.status_code}"
        )

    def get_all_repositories(self) -> list[dict[str, Any]]:
        """
        Fetch all repositories in the project.

        Returns:
            List of repository data dictionaries
        """
        repositories = []

        url = f"{self.base_url}/{self.project}/_apis/git/repositories?api-version={self.api_version}"
        print(f"Fetching repositories in project '{self.project}'...")

        try:
            response = self.session.get(url)
            self.check_rate_limit(response)

            if response.status_code == 200:
                data = response.json()
                repositories = data.get("value", [])
                print(f"Found {len(repositories)} repositories")
            elif response.status_code == 404:
                print(f"✗ Project '{self.project}' not found or not accessible")
            else:
                print(f"✗ Failed to fetch repositories: HTTP {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"✗ Error fetching repositories: {e}")

        return repositories

    def list_all_repositories(self) -> None:
        """List all repositories in the project with details."""
        print(f"\nFetching all repositories in project '{self.project}'...")

        repositories = self.get_all_repositories()

        if not repositories:
            print(f"No repositories found in project '{self.project}'.")
            return

        print(f"\nFound {len(repositories)} repositories in project '{self.project}':")
        print("=" * 80)

        for i, repo in enumerate(repositories, 1):
            name = repo.get("name", "Unknown")
            repo_id = repo.get("id", "Unknown")
            default_branch = repo.get("defaultBranch", "Unknown")
            size = repo.get("size", 0)
            is_disabled = repo.get("isDisabled", False)
            web_url = repo.get("webUrl", "")

            print(f"{i:3d}. {name}")
            print(f"     ID: {repo_id}")
            print(f"     Default Branch: {default_branch}")
            print(f"     Size: {size:,} bytes")
            print(f"     Disabled: {is_disabled}")
            if web_url:
                print(f"     URL: {web_url}")
            print()

    def delete_all_repositories(
        self,
        confirm: bool = False,
        exclude_patterns: list[str] | None = None,
        include_patterns: list[str] | None = None,
    ) -> list[dict]:
        """
        Delete all repositories in the project.

        Args:
            confirm: If True, skip confirmation prompt
            exclude_patterns: List of patterns to exclude from deletion
            include_patterns: List of patterns to include (if specified, only these will be deleted)

        Returns:
            List of deletion results
        """
        print(f"\nFetching all repositories in project '{self.project}'...")

        repositories = self.get_all_repositories()

        if not repositories:
            print(f"No repositories found in project '{self.project}'.")
            return []

        # Filter repositories based on include/exclude patterns
        repos_to_delete = []

        for repo in repositories:
            repo_name = repo.get("name", "")

            # Skip the default repository created with the project (usually has same name as project)
            if repo_name == self.project:
                print(f"Skipping default project repository: {repo_name}")
                continue

            # Check include patterns first (if specified)
            if include_patterns and not any(
                pattern in repo_name for pattern in include_patterns
            ):
                continue

            # Check exclude patterns
            if exclude_patterns and any(
                pattern in repo_name for pattern in exclude_patterns
            ):
                print(f"Skipping {repo_name} (matches exclude pattern)")
                continue

            repos_to_delete.append(repo)

        if not repos_to_delete:
            print("No repositories match the criteria for deletion.")
            return []

        print(
            f"\nRepositories to be deleted from project '{self.project}' ({len(repos_to_delete)}):"
        )
        print("=" * 50)

        for i, repo in enumerate(repos_to_delete, 1):
            name = repo.get("name", "Unknown")
            repo_id = repo.get("id", "Unknown")

            print(f"{i:3d}. {name} (ID: {repo_id})")

        # Confirmation prompt
        if not confirm:
            print(
                f"\n⚠️  WARNING: This will permanently delete {len(repos_to_delete)} repositories from project '{self.project}'!"
            )
            print("This action cannot be undone!")
            response = input(
                "\nAre you sure you want to continue? (type 'DELETE' to confirm): "
            )

            if response != "DELETE":
                print("Deletion cancelled.")
                return []

        print(f"\nStarting deletion of {len(repos_to_delete)} repositories...")

        # Extract repository info for deletion
        repo_info = [(repo["name"], repo["id"]) for repo in repos_to_delete]

        return self.cleanup_repositories(repo_info)

    def create_readme_content(
        self, repo_name: str, description: str | None = None
    ) -> str:
        """Generate README.md content for the repository."""
        content = f"""# {repo_name}

{description or f'Test repository {repo_name} for rate limiting testing.'}

## About
This repository was created as part of a bulk repository creation test for Azure DevOps API rate limiting analysis.

## Contents
- This README file
- Initial commit for testing purposes

## Created
Repository created on: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

---
*This is a test repository and may be deleted after testing is complete.*
"""
        return content

    def create_initial_commit(
        self, repo_id: str, repo_name: str, content: str, file_path: str = "README.md"
    ) -> dict[str, Any]:
        """
        Create an initial commit with a file in the repository.

        Args:
            repo_id: Repository ID
            repo_name: Repository name
            content: File content
            file_path: Path of the file to create

        Returns:
            API response data or error information
        """
        url = f"{self.base_url}/{self.project}/_apis/git/repositories/{repo_id}/pushes?api-version={self.api_version}"

        # Prepare the push payload
        payload = {
            "refUpdates": [
                {
                    "name": "refs/heads/main",
                    "oldObjectId": "0000000000000000000000000000000000000000",
                }
            ],
            "commits": [
                {
                    "comment": "Initial commit: Add README.md",
                    "changes": [
                        {
                            "changeType": "add",
                            "item": {"path": f"/{file_path}"},
                            "newContent": {
                                "content": content,
                                "contentType": "rawtext",
                            },
                        }
                    ],
                }
            ],
        }

        try:
            response = self.session.post(url, json=payload)
            self.check_rate_limit(response)

            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "repo_name": repo_name,
                    "commit_created": True,
                }
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                return {
                    "success": False,
                    "repo_name": repo_name,
                    "error": "rate_limited",
                    "retry_after": int(retry_after),
                    "response": response.text,
                }
            else:
                return {
                    "success": False,
                    "repo_name": repo_name,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text,
                }
        except Exception as e:
            return {"success": False, "repo_name": repo_name, "error": str(e)}

    def create_repository(
        self, repo_name: str, description: str | None = None
    ) -> dict[str, Any]:
        """
        Create a single repository with README and initial commit.

        Args:
            repo_name: Name of the repository
            description: Repository description

        Returns:
            API response data or error information
        """
        # Step 1: Create the repository
        url = f"{self.base_url}/{self.project}/_apis/git/repositories?api-version={self.api_version}"

        # Use project ID if available, otherwise use project name
        payload = {
            "name": repo_name,
            "project": {"id": self.project_id if self.project_id else self.project},
        }

        try:
            # Create repository
            response = self.session.post(url, json=payload)
            self.check_rate_limit(response)

            if response.status_code in [200, 201]:
                repo_data = response.json()
                repo_id = repo_data.get("id")

                # Step 2: Create README.md with initial commit
                readme_content = self.create_readme_content(repo_name, description)
                commit_result = self.create_initial_commit(
                    repo_id, repo_name, readme_content
                )

                if commit_result["success"]:
                    return {
                        "success": True,
                        "repo_name": repo_name,
                        "data": repo_data,
                        "readme_created": True,
                        "commit_created": True,
                    }
                else:
                    # Repository created but initial commit failed
                    return {
                        "success": True,  # Repo was created successfully
                        "repo_name": repo_name,
                        "data": repo_data,
                        "readme_created": False,
                        "commit_created": False,
                        "commit_error": commit_result.get("error"),
                    }

            elif response.status_code == 429:
                # Rate limited
                retry_after = response.headers.get("Retry-After", 60)
                return {
                    "success": False,
                    "repo_name": repo_name,
                    "error": "rate_limited",
                    "retry_after": int(retry_after),
                    "response": response.text,
                }
            elif response.status_code == 409:
                return {
                    "success": False,
                    "repo_name": repo_name,
                    "error": "Repository already exists",
                    "response": response.text,
                }
            elif response.status_code == 400:
                # Bad request - let's see what the actual error is
                error_msg = "HTTP 400 Bad Request"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = f"{error_msg}: {error_data['message']}"
                    else:
                        error_msg = f"{error_msg}: {error_data}"
                except Exception:
                    error_msg = f"{error_msg}: {response.text}"

                print(f"  Error details: {error_msg}")
                return {
                    "success": False,
                    "repo_name": repo_name,
                    "error": error_msg,
                    "response": response.text,
                }
            else:
                return {
                    "success": False,
                    "repo_name": repo_name,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text,
                }

        except Exception as e:
            return {"success": False, "repo_name": repo_name, "error": str(e)}

    def create_repositories_sequential(
        self, repo_names: list[str], delay_between_requests: float = 1.0
    ) -> list[dict]:
        """
        Create repositories sequentially with optional delay.

        Args:
            repo_names: List of repository names to create
            delay_between_requests: Delay in seconds between requests (default: 1.0 for Azure DevOps rate limits)

        Returns:
            List of results for each repository creation attempt
        """
        results = []

        for i, repo_name in enumerate(repo_names, 1):
            print(f"\nCreating repository {i}/{len(repo_names)}: {repo_name}")

            description = f"Test repository #{i} for rate limiting testing"
            result = self.create_repository(repo_name, description=description)
            results.append(result)

            if not result["success"]:
                if result.get("error") == "rate_limited":
                    retry_after = result.get("retry_after", 60)
                    print(f"Rate limited! Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    # Retry the request
                    result = self.create_repository(repo_name, description=description)
                    results[-1] = result
                else:
                    print(f"Failed to create {repo_name}: {result['error']}")
            else:
                status_msg = "✓ Repository"
                if result.get("readme_created"):
                    status_msg += " + README"
                if result.get("commit_created"):
                    status_msg += " + commit"
                print(f"{status_msg} created successfully")

            # Add delay between requests if specified
            if delay_between_requests > 0 and i < len(repo_names):
                time.sleep(delay_between_requests)

        return results

    def create_repositories_parallel(
        self, repo_names: list[str], max_workers: int = 3
    ) -> list[dict]:
        """
        Create repositories in parallel (more likely to trigger rate limits).
        Note: Azure DevOps has stricter rate limits, so we use fewer workers by default.

        Args:
            repo_names: List of repository names to create
            max_workers: Maximum number of concurrent requests (default: 3 for Azure DevOps)

        Returns:
            List of results for each repository creation attempt
        """
        results = []

        def create_single_repo(repo_name: str) -> dict[str, Any]:
            description = f"Test repository for rate limiting: {repo_name}"
            return self.create_repository(repo_name, description=description)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_repo = {
                executor.submit(create_single_repo, repo_name): repo_name
                for repo_name in repo_names
            }

            # Collect results as they complete
            for future in as_completed(future_to_repo):
                repo_name = future_to_repo[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result["success"]:
                        status = "✓"
                        details = []
                        if result.get("readme_created"):
                            details.append("README")
                        if result.get("commit_created"):
                            details.append("commit")
                        detail_str = f" ({', '.join(details)})" if details else ""
                        print(f"{status} {repo_name}: Success{detail_str}")
                    else:
                        print(f"✗ {repo_name}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    results.append(
                        {"success": False, "repo_name": repo_name, "error": str(e)}
                    )
                    print(f"✗ {repo_name}: Exception - {e}")

        return results

    def generate_repo_names(self, count: int, prefix: str = "test-repo") -> list[str]:
        """Generate a list of repository names."""
        timestamp = time.strftime("%Y%m%d-%H%M", time.gmtime())
        return [f"{prefix}-{timestamp}-{i:03d}" for i in range(1, count + 1)]

    def cleanup_repositories(self, repo_info: list[tuple[str, str]]) -> list[dict]:
        """
        Delete repositories (useful for cleanup after testing).

        Args:
            repo_info: List of tuples (repo_name, repo_id) to delete

        Returns:
            List of deletion results
        """
        results = []

        for i, (repo_name, repo_id) in enumerate(repo_info, 1):
            print(f"Deleting repository {i}/{len(repo_info)}: {repo_name}")
            url = f"{self.base_url}/{self.project}/_apis/git/repositories/{repo_id}?api-version={self.api_version}"

            try:
                response = self.session.delete(url)
                self.check_rate_limit(response)

                if response.status_code in [200, 204]:
                    results.append({"success": True, "repo_name": repo_name})
                    print(f"✓ Deleted {repo_name}")
                elif response.status_code == 404:
                    results.append(
                        {
                            "success": False,
                            "repo_name": repo_name,
                            "error": "Repository not found",
                        }
                    )
                    print(
                        f"⚠ Repository {repo_name} not found (may have been already deleted)"
                    )
                else:
                    results.append(
                        {
                            "success": False,
                            "repo_name": repo_name,
                            "error": f"HTTP {response.status_code}",
                        }
                    )
                    print(
                        f"✗ Failed to delete {repo_name}: HTTP {response.status_code}"
                    )

            except Exception as e:
                results.append(
                    {"success": False, "repo_name": repo_name, "error": str(e)}
                )
                print(f"✗ Failed to delete {repo_name}: {e}")

            # Small delay between deletions to avoid overwhelming the API
            if i < len(repo_info):
                time.sleep(0.5)  # Slightly longer delay for Azure DevOps

        return results

    def print_summary(self, results: list[dict]) -> None:
        """Print a summary of the operations."""
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        repos_with_readme = sum(1 for r in results if r.get("readme_created", False))
        repos_with_commits = sum(1 for r in results if r.get("commit_created", False))

        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"Total repositories: {len(results)}")
        print(f"Successfully processed: {successful}")
        if repos_with_readme > 0:
            print(f"With README files: {repos_with_readme}")
        if repos_with_commits > 0:
            print(f"With initial commits: {repos_with_commits}")
        print(f"Failed: {failed}")
        print(f"Total API requests made: {self.request_count}")

        if self.rate_limit_remaining is not None:
            print(f"Rate limit remaining: {self.rate_limit_remaining}")

        # Print failed repositories
        failed_repos = [r for r in results if not r["success"]]
        if failed_repos:
            print("\nFailed repositories:")
            for repo in failed_repos:
                print(f"  - {repo['repo_name']}: {repo.get('error', 'Unknown error')}")

        # Print partial successes (repo created but commit failed)
        partial_repos = [
            r
            for r in results
            if r.get("success") and not r.get("commit_created", False)
        ]
        if partial_repos:
            print("\nRepositories created but initial commit failed:")
            for repo in partial_repos:
                print(
                    f"  - {repo['repo_name']}: {repo.get('commit_error', 'Unknown error')}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create/manage bulk repositories in Azure DevOps using Personal Access Token"
    )
    parser.add_argument(
        "--pat", required=True, help="Azure DevOps Personal Access Token"
    )
    parser.add_argument(
        "--organization", required=True, help="Azure DevOps organization"
    )
    parser.add_argument("--project", required=True, help="Azure DevOps project name")
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of repos to create (default: 10)",
    )
    parser.add_argument(
        "--prefix",
        default="test-repo",
        help="Repository name prefix (default: test-repo)",
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Create repositories in parallel"
    )
    parser.add_argument(
        "--workers", type=int, default=3, help="Number of parallel workers (default: 3)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in sequential mode (default: 1.0)",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete repositories instead of creating them",
    )
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="Delete ALL repositories in the project (except default)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all repositories in the project",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        help="Include only repositories containing these patterns",
    )
    parser.add_argument(
        "--exclude", nargs="*", help="Exclude repositories containing these patterns"
    )
    parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--verify-token",
        action="store_true",
        help="Just verify the token and project then exit",
    )

    args = parser.parse_args()

    # Validate count for creation
    if (
        not args.cleanup
        and not args.delete_all
        and not args.list
        and not 1 <= args.count <= 100
    ):
        print("Warning: Count should be between 1-100 for rate limiting tests")
        print("Azure DevOps has stricter rate limits than other providers")

    # Initialize the creator
    creator = AzureDevOpsBulkCreator(args.pat, args.organization, args.project)

    # Verify token and project
    if not creator.verify_token():
        print("\n❌ Token verification failed.")
        print("\n💡 Troubleshooting tips:")
        print("1. Ensure your Personal Access Token is valid and not expired")
        print("2. Check that your PAT has 'Code (Read & Write)' permissions")
        print("3. Verify the organization name is correct")
        print("\nExample usage:")
        print(
            "  python script.py --pat YOUR_PAT --organization myorg --project myproject"
        )
        return

    if not creator.verify_project():
        print("\n❌ Project verification failed.")
        print("\n💡 Troubleshooting tips:")
        print("1. Check that the project name is correct")
        print("2. Ensure your PAT has access to this project")
        print("3. Verify the project exists in the specified organization")
        return

    if args.verify_token:
        print("✅ Token and project are valid!")
        return

    # Handle different operations
    if args.list:
        creator.list_all_repositories()
        return

    if args.delete_all:
        results = creator.delete_all_repositories(
            confirm=args.force,
            exclude_patterns=args.exclude,
            include_patterns=args.include,
        )
        creator.print_summary(results)
        return

    # Generate repository names for creation/cleanup
    repo_names = creator.generate_repo_names(args.count, args.prefix)

    print(
        f"\nStarting {'deletion' if args.cleanup else 'creation'} of {len(repo_names)} repositories in project '{args.project}'..."
    )
    print(f"Organization: {args.organization}")
    print(f"Project: {args.project}")
    print(f"Mode: {'Parallel' if args.parallel and not args.cleanup else 'Sequential'}")

    if args.parallel and not args.cleanup:
        print(f"Workers: {args.workers}")
        print(
            "Note: Azure DevOps has stricter rate limits, using conservative worker count"
        )

    # Execute the operation
    if args.cleanup:
        # For cleanup, we need to get the repository IDs first
        all_repos = creator.get_all_repositories()
        repo_info = []
        for repo_name in repo_names:
            matching_repo = next((r for r in all_repos if r["name"] == repo_name), None)
            if matching_repo:
                repo_info.append((repo_name, matching_repo["id"]))
            else:
                print(f"Repository {repo_name} not found, skipping")

        if repo_info:
            results = creator.cleanup_repositories(repo_info)
        else:
            print("No matching repositories found to delete")
            results = []
    elif args.parallel:
        results = creator.create_repositories_parallel(repo_names, args.workers)
    else:
        results = creator.create_repositories_sequential(repo_names, args.delay)

    # Print summary
    if results:
        creator.print_summary(results)


if __name__ == "__main__":
    main()
