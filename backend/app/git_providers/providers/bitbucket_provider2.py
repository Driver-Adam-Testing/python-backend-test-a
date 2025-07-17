import json
import logging
from typing import List, Dict, Optional, Tuple
from enum import Enum
from app.git_providers.interfaces.provider_interface import GitProviderInterface
from app.git_providers.interfaces.token_types import AccessTokenData, TokenType
from app.git_providers.core.config import GitProviderConfig
from app.git_providers.resources.bitbucket_api_resources import BitbucketAPIResources
from app.git_providers.utils.errors import GitProviderAccessTokenError
from app.git_providers.utils.git_provider_utils import generate_codebase_metadata
from app.schemas.git_provider_schema import GitRepository, GitProviderAppTokenSecret
from app.schemas.secret_management_schema import APP_INSTALL_WAT_NAME_PREFIX
from database.models_v1 import GitProviderApp, GitProviderAppInstallation
from shared.file_storage.aws_s3_client import AWSS3Client
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name
)

logger = logging.getLogger(__name__)


class BitbucketTokenType(str, Enum):
    """Bitbucket-specific token types"""
    WORKSPACE = "workspace_access_token"
    PROJECT = "project_access_token"
    REPOSITORY = "repository_access_token"


class BitbucketProvider(GitProviderInterface):
    """Bitbucket provider implementation supporting multiple access token types"""

    def __init__(self, config: GitProviderConfig, secrets_manager: AWSSecretManagementStrategy):
        self.config = config
        self.secrets_manager = secrets_manager
        self.api_strategy = BitbucketAPIResources(config.base_url)

    @classmethod
    def from_config(cls, app: GitProviderApp, aws_config: AWSClientConfig) -> 'BitbucketProvider':
        """Create BitbucketProvider from app configuration"""
        from app.git_providers.core.config_loader import load_provider_config

        secrets_manager = AWSSecretManagementStrategy(aws_config)
        config = load_provider_config(app, client_secret=None)

        return cls(config, secrets_manager)

    def validate_access_token(self, token_data: Dict) -> Tuple[bool, Optional[str]]:
        """Validate Bitbucket Access Token (Workspace, Project, or Repository)"""
        access_token = AccessTokenData(**token_data)

        # Map generic token types to Bitbucket-specific types
        if access_token.token_type == TokenType.WORKSPACE_ACCESS_TOKEN:
            bitbucket_type = BitbucketTokenType.WORKSPACE
        else:
            # Check metadata for specific Bitbucket token type
            bitbucket_type_str = access_token.token_type
            if bitbucket_type_str not in [t.value for t in BitbucketTokenType]:
                return False, f"Invalid Bitbucket token type: {bitbucket_type_str}"
            bitbucket_type = BitbucketTokenType(bitbucket_type_str)

        try:
            workspace_name = self.config.name
            is_valid, message = self.api_strategy.validate_workspace_access(
                workspace_name,
                access_token.token
            )
            # Validate based on token type
            # if bitbucket_type == BitbucketTokenType.WORKSPACE:
            #     is_valid, message = self.api_strategy.validate_workspace_access(
            #         access_token.workspace_or_group,
            #         access_token.token
            #     )
            # elif bitbucket_type == BitbucketTokenType.PROJECT:
            #     project_key = access_token.metadata.get("project_key")
            #     if not project_key:
            #         return False, "Project key required for project access token"
            #     is_valid, message = self.api_strategy.validate_project_access(
            #         access_token.workspace_or_group,
            #         project_key,
            #         access_token.token
            #     )
            # elif bitbucket_type == BitbucketTokenType.REPOSITORY:
            #     repo_slug = access_token.metadata.get("repository_slug")
            #     if not repo_slug:
            #         return False, "Repository slug required for repository access token"
            #     is_valid, message = self.api_strategy.validate_repository_access(
            #         access_token.workspace_or_group,
            #         repo_slug,
            #         access_token.token
            #     )
            # else:
            #     return False, f"Unsupported Bitbucket token type: {bitbucket_type}"

            return (is_valid, None) if is_valid else (False, message)

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False, str(e)

    def create_installation(self, organization_id: str, app_id: str,
                            token_data: Dict) -> GitProviderAppInstallation:
        """Create Bitbucket installation record"""
        access_token = AccessTokenData(**token_data)

        # Determine token type and scope
        # bitbucket_type_str = access_token.metadata.get(
        #     "bitbucket_token_type",
        #     BitbucketTokenType.WORKSPACE.value
        # )
        # bitbucket_type = BitbucketTokenType(bitbucket_type_str)

        # Build metadata based on token type
        metadata = {
            "kind": token_data["token_type"],
            "name": access_token.name,
            # "workspace": access_token.workspace_or_group,
            # "token_type": bitbucket_type.value
        }

        # if bitbucket_type == BitbucketTokenType.PROJECT:
        #     metadata["project_key"] = access_token.metadata.get("project_key")
        # elif bitbucket_type == BitbucketTokenType.REPOSITORY:
        #     metadata["repository_slug"] = access_token.metadata.get("repository_slug")

        return GitProviderAppInstallation(
            git_provider_app_id=app_id,
            organization_id=organization_id,
            misc_metadata=metadata
        )

    def store_secrets(self, installation: GitProviderAppInstallation,
                      token_data: Dict) -> None:
        """Store Bitbucket Access Token in AWS Secrets Manager"""
        access_token = AccessTokenData(**token_data)

        # Generate webhook secret
        import secrets
        webhook_secret = secrets.token_urlsafe(32)

        secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, str(installation.id))
        secret_value = json.dumps(
            GitProviderAppTokenSecret(
                token=access_token.token,
                secret_token=webhook_secret
            ).model_dump()
        )

        self.secrets_manager.write_secret(secret_key, secret_value)
        logger.info(f"Stored WAT for Bitbucket installation {installation.id}")

    def fetch_secrets(self, installation: GitProviderAppInstallation) -> dict:
        """Fetch stored secrets for a Bitbucket installation"""
        secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, str(installation.id))
        secret_value = self.secrets_manager.read_secret(secret_key)

        if not secret_value:
            raise ValueError(f"Access token not found for installation: {installation.id}")

        return secret_value

    def fetch_repositories(self, installation: GitProviderAppInstallation) -> List[GitRepository]:
        """Fetch Bitbucket repositories based on token type"""
        logger.info(f"Fetching repositories for installation: {installation.id}")

        try:
            # Get token and metadata from secrets
            secrets = self.fetch_secrets(installation)
            access_token = secrets["token"]

            # token_type = BitbucketTokenType(secrets.get("token_type", BitbucketTokenType.WORKSPACE.value))
            token_type = BitbucketTokenType(installation.misc_metadata["kind"])
            # workspace = installation.misc_metadata["name"]
            workspace = installation.git_provider_app.name

            # Fetch repositories based on token type
            repos_data = self.api_strategy.list_repositories(workspace, access_token)
            # if token_type == BitbucketTokenType.WORKSPACE:
            #
            # elif token_type == BitbucketTokenType.PROJECT:
            #     project_key = secrets.get("project_key")
            #     if not project_key:
            #         raise ValueError("Project key not found in secrets")
            #     repos_data = self.api_strategy.list_project_repositories(
            #         workspace, project_key, access_token
            #     )
            #
            # elif token_type == BitbucketTokenType.REPOSITORY:
            #     repo_slug = secrets.get("repository_slug")
            #     if not repo_slug:
            #         raise ValueError("Repository slug not found in secrets")
            #     # For single repository, fetch just that one
            #     repo_data = self.api_strategy.get_repository(
            #         workspace, repo_slug, access_token
            #     )
            #     repos_data = [repo_data] if repo_data else []
            #
            # else:
            #     raise ValueError(f"Unsupported token type: {token_type}")

            # Convert to GitRepository objects
            repos = []
            for repo in repos_data:
                # Fetch latest commit for each repo if needed
                latest_commit = None
                try:
                    commit_hash = self.api_strategy.get_latest_commit(
                        workspace, repo["slug"], access_token
                    )
                    latest_commit = {"id": commit_hash}
                except Exception as e:
                    logger.warning(f"Failed to fetch latest commit for {repo['name']}: {e}")

                repos.append(GitRepository(
                    org=repo["owner"]["display_name"],
                    installation_id=str(installation.id),
                    provider_kind=installation.git_provider_app.provider_kind,
                    provider_name=str(installation.git_provider_app.provider_kind),
                    repo_name=repo["name"],
                    repo_id=repo["uuid"],
                    repo_full_name=repo["full_name"],
                    repo_url=repo["links"]["html"]["href"],
                    latest_commit=latest_commit,
                    last_updated=repo.get("updated_on"),
                    metadata={
                        "workspace": workspace,
                        "slug": repo["slug"],
                        "project_key": repo.get("project", {}).get("key"),
                        "is_private": repo.get("is_private", True),
                        "language": repo.get("language"),
                        "created_on": repo.get("created_on"),
                        "updated_on": repo.get("updated_on")
                    }
                ))

            logger.info(f"Fetched {len(repos)} repositories for installation {installation.id}")
            return repos

        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}")
            raise

    def clone_repository(self, repo_info: GitRepository, user_id: str,
                         org_id: str, upload_key: str, bucket_name: str) -> str:
        """Clone Bitbucket repository and upload to S3"""
        logger.info(f"Cloning Bitbucket repository: {repo_info.repo_name}")

        try:
            # Get access token from installation
            installation_id = repo_info.installation_id
            secrets = self.fetch_secrets_by_id(installation_id)
            access_token = secrets["token"]
            token_type = BitbucketTokenType(secrets.get("token_type", BitbucketTokenType.WORKSPACE.value))

            # Verify access to repository based on token type
            workspace = repo_info.metadata["workspace"]
            repo_slug = repo_info.metadata["slug"]

            if token_type == BitbucketTokenType.PROJECT:
                # Verify repo belongs to the project
                project_key = secrets.get("project_key")
                repo_project = repo_info.metadata.get("project_key")
                if repo_project != project_key:
                    raise ValueError(f"Repository not in authorized project: {project_key}")

            elif token_type == BitbucketTokenType.REPOSITORY:
                # Verify it's the authorized repository
                authorized_repo = secrets.get("repository_slug")
                if repo_slug != authorized_repo:
                    raise ValueError(f"Not authorized for repository: {repo_slug}")

            # Get latest commit if not specified
            commit = repo_info.latest_commit.get("id") if repo_info.latest_commit else None
            if not commit:
                logger.warning(f"No commit specified for {repo_info.repo_name}, fetching latest")
                commit = self.api_strategy.get_latest_commit(
                    workspace, repo_slug, access_token
                )

            # Download repository
            logger.info(f"Downloading repository {workspace}/{repo_slug} at commit {commit}")
            zip_content = self.api_strategy.download_repo(
                workspace, repo_slug, commit, access_token
            )

            # Generate metadata
            metadata = generate_codebase_metadata(
                org_id=org_id,
                org_name=workspace,
                repo=repo_info.repo_name,
                repo_id=repo_info.repo_id,
                owner=workspace,
                provider="bitbucket",
                commit=commit,
                upload_key=upload_key
            )

            # Upload to S3
            logger.info(f"Uploading repository to S3: {upload_key}")
            s3_client = AWSS3Client(self.secrets_manager.aws_config)

            upload_success = s3_client.upload_to_s3(
                file_content=zip_content,
                bucket_name=bucket_name,
                s3_key=upload_key,
                metadata_dict=metadata
            )

            if not upload_success:
                raise ValueError("Failed to upload repository to S3")

            # Generate presigned URL
            download_url = s3_client.generate_get_presigned_url(bucket_name, upload_key)
            logger.info(f"Repository cloned successfully: {repo_info.repo_name}")

            return download_url

        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

    def handle_webhook(self, event_type: str, payload: Dict,
                       installation_id: str) -> Dict:
        """Handle Bitbucket webhook events"""
        logger.info(f"Handling Bitbucket webhook: {event_type} for installation {installation_id}")

        try:
            # Bitbucket event types are prefixed (e.g., "repo:push")
            if event_type == "repo:push":
                return self._handle_push_event(payload, installation_id)
            elif event_type == "pullrequest:created" or event_type == "pullrequest:updated":
                return self._handle_pull_request_event(payload, installation_id, event_type)
            elif event_type == "repo:fork":
                return self._handle_fork_event(payload, installation_id)
            else:
                logger.info(f"Ignoring Bitbucket event type: {event_type}")
                return {"status": "ignored", "event": event_type}

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            raise

    def revoke_access(self, installation: GitProviderAppInstallation) -> None:
        """Revoke access for a Bitbucket installation"""
        logger.info(f"Revoking access for Bitbucket installation {installation.id}")

        # Delete access token secret
        secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, str(installation.id))
        self.secrets_manager.delete_secret(secret_key)
        logger.info(f"Deleted access token secret for installation {installation.id}")

    # Private helper methods

    def fetch_secrets_by_id(self, installation_id: str) -> dict:
        """Fetch secrets by installation ID"""
        secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, installation_id)
        secret_value = self.secrets_manager.read_secret(secret_key)

        if not secret_value:
            raise ValueError(f"Access token not found for installation: {installation_id}")

        # Handle both old format (direct token) and new format (dict)
        if isinstance(secret_value, str):
            # Legacy format - assume workspace token
            return {"token": secret_value, "token_type": BitbucketTokenType.WORKSPACE.value}

        return secret_value

    def _handle_push_event(self, payload: Dict, installation_id: str) -> Dict:
        """Handle push webhook event"""
        push = payload.get("push", {})
        repository = payload.get("repository", {})
        changes = push.get("changes", [])

        logger.info(f"Push event for repository {repository.get('name')} with {len(changes)} changes")

        # Extract branch info from changes
        branches = []
        commits_count = 0

        for change in changes:
            if change.get("new", {}).get("type") == "branch":
                branch_name = change["new"]["name"]
                branches.append(branch_name)
                commits_count += len(change.get("commits", []))

        return {
            "status": "processed",
            "event": "push",
            "repository": repository.get("name"),
            "branches": branches,
            "commits": commits_count
        }

    def _handle_pull_request_event(self, payload: Dict, installation_id: str, event_type: str) -> Dict:
        """Handle pull request webhook event"""
        pullrequest = payload.get("pullrequest", {})
        action = event_type.split(":")[-1]  # Extract action from event type

        logger.info(f"Pull request event: {action} for PR {pullrequest.get('id')}")

        return {
            "status": "processed",
            "event": "pull_request",
            "action": action,
            "pull_request_id": pullrequest.get("id"),
            "title": pullrequest.get("title")
        }

    def _handle_fork_event(self, payload: Dict, installation_id: str) -> Dict:
        """Handle fork webhook event"""
        repository = payload.get("repository", {})
        fork = payload.get("fork", {})

        logger.info(f"Fork event for repository {repository.get('name')}")

        return {
            "status": "processed",
            "event": "fork",
            "original_repository": repository.get("name"),
            "fork_name": fork.get("name"),
            "fork_owner": fork.get("owner", {}).get("display_name")
        }