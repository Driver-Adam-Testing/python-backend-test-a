import logging

import gitlab
import httpx
from app.git_providers.utils.errors import GitProviderAccessTokenError
from app.schemas.git_provider_schema import GitRepository
from database.models import GitProviderKind

logger = logging.getLogger(__name__)


class GitLabAPIResources:
    def __init__(
        self,
        base_url: str,
        provider_kind: GitProviderKind,
    ) -> None:
        self.base_url = base_url
        self.provider_kind = provider_kind

    # TODO: add pagination
    def fetch_repos(
        self,
        app_install_id: str,
        access_token: str,
    ) -> list[GitRepository]:
        gl = gitlab.Gitlab(
            self.base_url,
            oauth_token=access_token,
            keep_base_url=True,
        )
        repos = []
        try:
            # Authenticate the client
            gl.auth()

            # Retrieve projects the user is a member of
            projects = gl.projects.list(membership=True, get_all=True)

            # Extract Repository Information and get latest commit details
            for project in projects:
                detailed_project = gl.projects.get(project.id)
                repo_url = detailed_project.http_url_to_repo
                default_branch = detailed_project.default_branch

                # Fetch the latest commit from the default branch
                commits = detailed_project.commits.list(
                    ref_name=default_branch, page=1, per_page=1
                )
                if not commits:
                    logger.warning(
                        f"GitLab: No commits found for the project {detailed_project.name} for url {repo_url}."
                    )
                    continue
                else:
                    latest_commit = commits[0]

                commit_info = {
                    "repository_url": repo_url,
                    "default_branch": default_branch,
                }

                if latest_commit is not None:
                    commit_info["commit"] = {
                        "id": latest_commit.id,
                        "message": latest_commit.message,
                        "author": latest_commit.author_name,
                        "date": str(latest_commit.committed_date),
                    }

                git_repo = GitRepository(
                    provider_name=self.provider_kind.name.replace("_", " ").title(),
                    provider_kind=self.provider_kind,
                    repo_name=detailed_project.name,
                    org=detailed_project.namespace["full_path"],
                    last_updated=latest_commit.committed_date,
                    default_branch=default_branch,
                    latest_commit=commit_info,
                    metadata=detailed_project.asdict(),
                    installation_id=str(app_install_id),
                )
                repos.append(git_repo)

        except gitlab.exceptions.GitlabAuthenticationError:
            logger.error("Authentication failed. Check your access token.")
            raise GitProviderAccessTokenError("Authentication failed.")
        except gitlab.exceptions.GitlabGetError:
            logger.error(
                "Failed to fetch data from GitLab. Check your network connection or permissions."
            )
            raise
        return repos

    def fetch_project(
        self,
        project_id: str,
        access_token: str,
    ) -> dict | None:
        gl = gitlab.Gitlab(
            self.base_url,
            oauth_token=access_token,
            keep_base_url=True,
        )
        gl.auth()
        try:
            # Authenticate the client

            # Retrieve projects the user is a member of
            project = gl.projects.get(project_id)
            return project.asdict()
        except gitlab.exceptions.GitlabAuthenticationError:
            logger.error("Authentication failed. Check your access token.")
        except gitlab.exceptions.GitlabGetError:
            logger.error(
                "Failed to fetch data from GitLab. Check your network connection or permissions."
            )
        return None

    def download_repo(self, repo_id: str, commit: str, access_token: str) -> bytes:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = httpx.get(
            f"{self.base_url}/api/v4/projects/{repo_id}/repository/archive.zip?sha={commit}",
            headers=headers,
            timeout=120,
        )
        response.raise_for_status()
        return response.content
