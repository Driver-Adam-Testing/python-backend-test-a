#!/usr/bin/env python3
"""
Bitbucket Bulk Repository Creator with Access Token Authentication
Creates multiple repositories in a Bitbucket workspace for rate limiting tests.
Works with Google login users via access tokens.
Updated with ability to delete all repositories in a workspace or specific project.
"""

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests


class BitbucketBulkCreator:
    def __init__(
        self,
        access_token: str,
        workspace: str,
        username: str | None = None,
        project_key: str | None = None,
    ) -> None:
        """
        Initialize the Bitbucket API client with access token.

        Args:
            access_token: Bitbucket access token
            workspace: Workspace name/UUID where repos will be created
            username: Username (for app password authentication)
            project_key: Optional project key to filter repositories
        """
        self.access_token = access_token
        self.workspace = workspace
        self.project_key = project_key
        self.base_url = "https://api.bitbucket.org/2.0"
        self.session = requests.Session()
        print(f"Using workspace: {self.workspace}")
        if self.project_key:
            print(f"Using project: {self.project_key}")
        print(
            f"Using access token: {'*' * (len(access_token) - 4) + access_token[-4:]}"
        )
        # Set up authorization header
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Rate limiting tracking
        self.request_count = 0
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

    def verify_token(self) -> bool:
        """Verify that the access token is valid."""
        try:
            response = self.session.get(f"{self.base_url}/user")
            if response.status_code == 200:
                user_data = response.json()
                print(
                    f"✓ Token verified for user: {user_data.get('display_name', 'Unknown')}"
                )
                return True
            else:
                print(f"✗ Token verification failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Token verification error: {e}")
            return False

    def check_rate_limit(self, response: requests.Response) -> None:
        """Extract and track rate limit information from response headers."""
        self.request_count += 1

        # Bitbucket rate limit headers
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in response.headers:
            self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])

        print(
            f"Request #{self.request_count} | "
            f"Rate Limit Remaining: {self.rate_limit_remaining} | "
            f"Status: {response.status_code}"
        )

    def get_all_repositories(self) -> list[dict[str, Any]]:
        """
        Fetch all repositories in the workspace, optionally filtered by project.

        Returns:
            List of repository data dictionaries
        """
        repositories = []

        # Build URL based on whether we're filtering by project
        if self.project_key:
            url = f'{self.base_url}/repositories/{self.workspace}?q=project.key="{self.project_key}"'
            print(f"Fetching repositories in project '{self.project_key}'...")
        else:
            url = f"{self.base_url}/repositories/{self.workspace}"
            print("Fetching all repositories in workspace...")

        while url:
            try:
                response = self.session.get(url)
                self.check_rate_limit(response)

                if response.status_code == 200:
                    data = response.json()
                    batch_repos = data.get("values", [])
                    repositories.extend(batch_repos)

                    # Check for next page
                    url = data.get("next")

                    if url:
                        print(
                            f"Fetched {len(batch_repos)} repositories, getting next page..."
                        )
                        time.sleep(0.1)  # Small delay between pages

                elif response.status_code == 404:
                    if self.project_key:
                        print(
                            f"✗ Project '{self.project_key}' not found in workspace '{self.workspace}' or not accessible"
                        )
                    else:
                        print(
                            f"✗ Workspace '{self.workspace}' not found or not accessible"
                        )
                    break
                else:
                    print(
                        f"✗ Failed to fetch repositories: HTTP {response.status_code}"
                    )
                    print(f"Response: {response.text}")
                    break

            except Exception as e:
                print(f"✗ Error fetching repositories: {e}")
                break

        return repositories

    def get_all_projects(self) -> list[dict[str, Any]]:
        """
        Fetch all projects in the workspace.

        Returns:
            List of project data dictionaries
        """
        projects = []
        url = f"{self.base_url}/workspaces/{self.workspace}/projects"

        while url:
            try:
                response = self.session.get(url)
                self.check_rate_limit(response)

                if response.status_code == 200:
                    data = response.json()
                    projects.extend(data.get("values", []))

                    # Check for next page
                    url = data.get("next")

                    if url:
                        print(
                            f"Fetched {len(data.get('values', []))} projects, getting next page..."
                        )
                        time.sleep(0.1)

                elif response.status_code == 404:
                    print(f"✗ Workspace '{self.workspace}' not found or not accessible")
                    break
                else:
                    print(f"✗ Failed to fetch projects: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    break

            except Exception as e:
                print(f"✗ Error fetching projects: {e}")
                break

        return projects

    def list_all_projects(self) -> None:
        """List all projects in the workspace with details."""
        print(f"\nFetching all projects in workspace '{self.workspace}'...")
        projects = self.get_all_projects()

        if not projects:
            print("No projects found or failed to fetch projects.")
            return

        print(f"\nFound {len(projects)} projects:")
        print("=" * 80)

        for i, project in enumerate(projects, 1):
            name = project.get("name", "Unknown")
            key = project.get("key", "Unknown")
            description = project.get("description", "No description")
            created_on = project.get("created_on", "Unknown")
            is_private = project.get("is_private", False)

            print(f"{i:3d}. {name} (Key: {key})")
            print(f"     Description: {description}")
            print(f"     Private: {is_private}")
            print(f"     Created: {created_on}")
            print()

    def list_all_repositories(self) -> None:
        """List all repositories in the workspace/project with details."""
        if self.project_key:
            print(
                f"\nFetching all repositories in project '{self.project_key}' (workspace: '{self.workspace}')..."
            )
        else:
            print(f"\nFetching all repositories in workspace '{self.workspace}'...")

        repositories = self.get_all_repositories()

        if not repositories:
            if self.project_key:
                print(
                    f"No repositories found in project '{self.project_key}' or failed to fetch repositories."
                )
            else:
                print("No repositories found or failed to fetch repositories.")
            return

        context = (
            f"project '{self.project_key}'"
            if self.project_key
            else f"workspace '{self.workspace}'"
        )
        print(f"\nFound {len(repositories)} repositories in {context}:")
        print("=" * 80)

        for i, repo in enumerate(repositories, 1):
            name = repo.get("name", "Unknown")
            full_name = repo.get("full_name", "Unknown")
            is_private = repo.get("is_private", False)
            created_on = repo.get("created_on", "Unknown")
            size = repo.get("size", 0)
            language = repo.get("language", "Unknown")
            project_info = repo.get("project", {})
            project_name = (
                project_info.get("name", "No project") if project_info else "No project"
            )
            project_key = project_info.get("key", "N/A") if project_info else "N/A"

            print(f"{i:3d}. {name}")
            print(f"     Full name: {full_name}")
            print(f"     Project: {project_name} ({project_key})")
            print(f"     Private: {is_private}")
            print(f"     Created: {created_on}")
            print(f"     Size: {size} bytes")
            print(f"     Language: {language}")
            print()

    def delete_all_repositories(
        self,
        confirm: bool = False,
        exclude_patterns: list[str] | None = None,
        include_patterns: list[str] | None = None,
    ) -> list[dict]:
        """
        Delete all repositories in the workspace/project.

        Args:
            confirm: If True, skip confirmation prompt
            exclude_patterns: List of patterns to exclude from deletion
            include_patterns: List of patterns to include (if specified, only these will be deleted)

        Returns:
            List of deletion results
        """
        if self.project_key:
            print(
                f"\nFetching all repositories in project '{self.project_key}' (workspace: '{self.workspace}')..."
            )
        else:
            print(f"\nFetching all repositories in workspace '{self.workspace}'...")

        repositories = self.get_all_repositories()

        if not repositories:
            context = (
                f"project '{self.project_key}'" if self.project_key else "workspace"
            )
            print(f"No repositories found in {context}.")
            return []

        # Filter repositories based on include/exclude patterns
        repos_to_delete = []

        for repo in repositories:
            repo_name = repo.get("name", "")

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

        context = (
            f"project '{self.project_key}'"
            if self.project_key
            else f"workspace '{self.workspace}'"
        )
        print(f"\nRepositories to be deleted from {context} ({len(repos_to_delete)}):")
        print("=" * 50)

        for i, repo in enumerate(repos_to_delete, 1):
            name = repo.get("name", "Unknown")
            is_private = repo.get("is_private", False)
            project_info = repo.get("project", {})
            project_name = (
                project_info.get("name", "No project") if project_info else "No project"
            )
            project_key = project_info.get("key", "N/A") if project_info else "N/A"

            print(f"{i:3d}. {name} ({'private' if is_private else 'public'})")
            print(f"     Project: {project_name} ({project_key})")

        # Confirmation prompt
        if not confirm:
            warning_context = (
                f"project '{self.project_key}'"
                if self.project_key
                else f"workspace '{self.workspace}'"
            )
            print(
                f"\n⚠️  WARNING: This will permanently delete {len(repos_to_delete)} repositories from {warning_context}!"
            )
            print("This action cannot be undone!")
            response = input(
                "\nAre you sure you want to continue? (type 'DELETE' to confirm): "
            )

            if response != "DELETE":
                print("Deletion cancelled.")
                return []

        print(f"\nStarting deletion of {len(repos_to_delete)} repositories...")

        # Extract repository names for deletion
        repo_names = [repo["name"] for repo in repos_to_delete]

        return self.cleanup_repositories(repo_names)

    def create_readme_content(
        self, repo_name: str, description: str | None = None
    ) -> str:
        """Generate README.md content for the repository."""
        content = f"""# {repo_name}

{description or f'Test repository {repo_name} for rate limiting testing.'}

## About
This repository was created as part of a bulk repository creation test for Bitbucket API rate limiting analysis.

## Contents
- This README file
- Initial commit for testing purposes

## Created
Repository created on: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

---
*This is a test repository and may be deleted after testing is complete.*
"""
        return content

    def create_file_in_repository(
        self, repo_name: str, file_path: str, content: str, commit_message: str
    ) -> dict[str, Any]:
        """
        Create a file in the repository with a commit using the src endpoint.

        Args:
            repo_name: Name of the repository
            file_path: Path of the file to create (e.g., 'README.md')
            content: File content
            commit_message: Commit message

        Returns:
            API response data or error information
        """
        url = f"{self.base_url}/repositories/{self.workspace}/{repo_name}/src"

        # Use multipart form data for file upload
        files = {file_path: (file_path, content, "text/plain")}

        data = {"message": commit_message, "branch": "main"}

        # Remove Content-Type header for multipart upload
        headers = self.session.headers.copy()
        if "Content-Type" in headers:
            del headers["Content-Type"]

        try:
            response = requests.post(url, files=files, data=data, headers=headers)
            self.check_rate_limit(response)

            if response.status_code in [201, 200]:
                return {
                    "success": True,
                    "repo_name": repo_name,
                    "file_path": file_path,
                    "data": response.json() if response.content else {},
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
        self, repo_name: str, is_private: bool = True, description: str | None = None
    ) -> dict[str, Any]:
        """
        Create a single repository with README and initial commit.

        Args:
            repo_name: Name of the repository
            is_private: Whether the repository should be private
            description: Repository description

        Returns:
            API response data or error information
        """
        # Step 1: Create the repository
        url = f"{self.base_url}/repositories/{self.workspace}/{repo_name}"

        payload = {
            "name": repo_name,
            "is_private": is_private,
            "scm": "git",
            "has_issues": False,
            "has_wiki": False,
            "fork_policy": "no_public_forks" if is_private else "allow_forks",
        }

        if description:
            payload["description"] = description

        # Add project association if project_key is specified
        if self.project_key:
            payload["project"] = {"key": self.project_key}

        try:
            # Create repository
            response = self.session.post(url, json=payload)
            self.check_rate_limit(response)

            if response.status_code == 200:
                repo_data = response.json()

                # Step 2: Create README.md with initial commit
                readme_content = self.create_readme_content(repo_name, description)
                readme_result = self.create_file_in_repository(
                    repo_name,
                    "README.md",
                    readme_content,
                    "Initial commit: Add README.md",
                )

                if readme_result["success"]:
                    return {
                        "success": True,
                        "repo_name": repo_name,
                        "data": repo_data,
                        "readme_created": True,
                        "commit_created": True,
                    }
                else:
                    # Repository created but README failed
                    return {
                        "success": False,
                        "repo_name": repo_name,
                        "error": f"Repository created but README failed: {readme_result['error']}",
                        "repo_created": True,
                        "readme_created": False,
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
        self, repo_names: list[str], delay_between_requests: float = 0.1
    ) -> list[dict]:
        """
        Create repositories sequentially with optional delay.

        Args:
            repo_names: List of repository names to create
            delay_between_requests: Delay in seconds between requests

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
        self, repo_names: list[str], max_workers: int = 5
    ) -> list[dict]:
        """
        Create repositories in parallel (more likely to trigger rate limits).

        Args:
            repo_names: List of repository names to create
            max_workers: Maximum number of concurrent requests

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
        return [f"{prefix}-{i:03d}" for i in range(1, count + 1)]

    def cleanup_repositories(self, repo_names: list[str]) -> list[dict]:
        """
        Delete repositories (useful for cleanup after testing).

        Args:
            repo_names: List of repository names to delete

        Returns:
            List of deletion results
        """
        results = []

        for i, repo_name in enumerate(repo_names, 1):
            print(f"Deleting repository {i}/{len(repo_names)}: {repo_name}")
            url = f"{self.base_url}/repositories/{self.workspace}/{repo_name}"

            try:
                response = self.session.delete(url)
                self.check_rate_limit(response)

                if response.status_code == 204:
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
            if i < len(repo_names):
                time.sleep(0.1)

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
                print(f"  - {repo['repo_name']}: {repo['error']}")

        # Print partial successes (repo created but README failed)
        partial_repos = [
            r for r in results if r.get("repo_created") and not r.get("readme_created")
        ]
        if partial_repos:
            print("\nRepositories created but README failed:")
            for repo in partial_repos:
                print(f"  - {repo['repo_name']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create/manage bulk repositories in Bitbucket using access token"
    )
    parser.add_argument(
        "--token", required=True, help="Bitbucket access token or app password"
    )
    parser.add_argument("--username", help="Username (required if using app password)")
    parser.add_argument("--workspace", required=True, help="Bitbucket workspace")
    parser.add_argument(
        "--project", help="Bitbucket project key (optional - filters to project only)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of repos to create (default: 100)",
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
        "--workers", type=int, default=5, help="Number of parallel workers (default: 5)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between requests in sequential mode (default: 0.1)",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete repositories instead of creating them",
    )
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="Delete ALL repositories in the workspace/project",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all repositories in the workspace/project",
    )
    parser.add_argument(
        "--list-projects",
        action="store_true",
        help="List all projects in the workspace",
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
        "--verify-token", action="store_true", help="Just verify the token and exit"
    )

    args = parser.parse_args()

    # Validate count for creation
    if (
        not args.cleanup
        and not args.delete_all
        and not args.list
        and not args.list_projects
        and not 1 <= args.count <= 200
    ):
        print("Warning: Count should be between 1-200 for rate limiting tests")

    # Initialize the creator
    creator = BitbucketBulkCreator(
        args.token, args.workspace, args.username, args.project
    )

    # Verify token first (unless just listing)
    # if not args.list and not args.list_projects and not creator.verify_token():
    #     print("\n❌ Token verification failed.")
    #     print("\n💡 Troubleshooting tips:")
    #     print(
    #         "1. If using Repository Access Token: Make sure it starts with 'ATBB' and has 'Repositories: Write' permission")
    #     print("2. If using App Password: Provide your username with --username flag")
    #     print("3. Check that your workspace name is correct")
    #     print("4. Ensure the token hasn't expired")
    #     print("\nExample usage:")
    #     print("  Repository token: python script.py --token ATBB... --workspace myworkspace")
    #     print("  App password: python script.py --token apppassword --username myusername --workspace myworkspace")
    #     print("  With project: python script.py --token ATBB... --workspace myworkspace --project MYPROJ")
    #     sys.exit(1)
    #
    # if args.verify_token:
    #     print("✅ Token is valid!")
    #     sys.exit(0)

    # Handle different operations
    if args.list_projects:
        creator.list_all_projects()
        return

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

    context = (
        f"project '{args.project}'" if args.project else f"workspace '{args.workspace}'"
    )
    print(
        f"\nStarting {'deletion' if args.cleanup else 'creation'} of {len(repo_names)} repositories in {context}..."
    )
    print(f"Workspace: {args.workspace}")
    if args.project:
        print(f"Project: {args.project}")
    print(f"Mode: {'Parallel' if args.parallel and not args.cleanup else 'Sequential'}")

    # Execute the operation
    if args.cleanup:
        results = creator.cleanup_repositories(repo_names)
    elif args.parallel:
        results = creator.create_repositories_parallel(repo_names, args.workers)
    else:
        results = creator.create_repositories_sequential(repo_names, args.delay)

    # Print summary
    creator.print_summary(results)


if __name__ == "__main__":
    main()
