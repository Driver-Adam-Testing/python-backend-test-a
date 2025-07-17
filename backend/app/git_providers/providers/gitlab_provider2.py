import json
import logging
from typing import List, Dict, Optional, Tuple
from app.git_providers.interfaces.provider_interface import GitProviderInterface
from app.git_providers.interfaces.token_types import AccessTokenData, TokenType
from app.git_providers.core.config import GitProviderConfig
from app.git_providers.oauth.gitlab_oauth_strategy import GitLabOAuthStrategy
from app.git_providers.resources.gitlab_resources import GitLabAPIResources
from app.git_providers.utils.errors import GitProviderAccessTokenError
from app.git_providers.utils.git_provider_utils import generate_codebase_metadata
from app.schemas.git_provider_schema import GitRepository, GitProviderAppTokenSecret
from app.schemas.secret_management_schema import (
    APP_INSTALL_GAT_NAME_PREFIX,
    APP_SECRET_NAME_PREFIX
)
from database.models_v1 import GitProviderApp, GitProviderAppInstallation
from shared.file_storage.aws_s3_client import AWSS3Client
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name
)

logger = logging.getLogger(__name__)


class GitLabProvider(GitProviderInterface):
    """GitLab provider implementation supporting Group Access Tokens only"""



    def __init__(self, config: GitProviderConfig, secrets_manager: AWSSecretManagementStrategy):
        self.config = config
        self.secrets_manager = secrets_manager
        self.auth_strategy = GitLabOAuthStrategy(config)  # Still used for token validation
        self.api_strategy = GitLabAPIResources(config.base_url, config.provider_kind)

    @classmethod
    def from_config(cls, app: GitProviderApp, aws_config: AWSClientConfig) -> 'GitLabProvider':
        """Create GitLabProvider from app configuration"""
        from app.git_providers.core.config_loader import load_provider_config

        secrets_manager = AWSSecretManagementStrategy(aws_config)

        # GitLab with GAT doesn't need app-level secrets
        config = load_provider_config(app, client_secret=None)

        return cls(config, secrets_manager)

    #TODO: revisit this throw error vs return False
    def validate_access_token(self, token_data: Dict) -> Tuple[bool, Optional[str]]:
        """Validate GitLab Group Access Token"""
        access_token = AccessTokenData(**token_data)

        if access_token.token_type != TokenType.GROUP_ACCESS_TOKEN:
            return False, "GitLab only supports Group Access Tokens"

        # Validate GAT by attempting to get user info
        try:
            user = self.auth_strategy.token_user(access_token.token)
            return (True, None) if user else (False, "Invalid token")
        except Exception as e:
            logger.error(f"GAT validation failed: {e}")
            return False, str(e)

    def create_installation(self, organization_id: str, app_id: str,
                            token_data: Dict) -> GitProviderAppInstallation:
        """Create GitLab installation record"""
        access_token = AccessTokenData(**token_data)
        return GitProviderAppInstallation(
            git_provider_app_id=app_id,
            organization_id=organization_id,
            misc_metadata={
                "kind": token_data["token_type"],
                "name": access_token.name,
            }
        )

    def store_secrets(self, installation: GitProviderAppInstallation,
                      token_data: Dict) -> None:
        """Store GitLab GAT in AWS Secrets Manager"""
        access_token = AccessTokenData(**token_data)

        # Generate webhook secret
        import secrets
        webhook_secret = secrets.token_urlsafe(32)

        secret_key = format_secret_name(APP_INSTALL_GAT_NAME_PREFIX, str(installation.id))
        secret_value = json.dumps(
            GitProviderAppTokenSecret(
                token=access_token.token, secret_token=webhook_secret
            ).model_dump()
        )
        self.secrets_manager.write_secret(secret_key, secret_value)
        logger.info(f"Stored GAT for GitLab installation {installation.id}")
    def fetch_secrets(self, installation: GitProviderAppInstallation) -> dict:
        secret_key = format_secret_name(APP_INSTALL_GAT_NAME_PREFIX, installation.id)
        secret_value = self.secrets_manager.read_secret(secret_key)
        if not secret_value:
            raise ValueError(f"GAT not found for installation: {installation.id}")
        return secret_value
    def fetch_repositories(self, installation: GitProviderAppInstallation) -> List[GitRepository]:
        """Fetch GitLab repositories using GAT"""
        logger.info(f"Fetching repositories for installation: {installation.id}")

        try:
            access_token = self._fetch_group_access_token(str(installation.id))

            # Use the API strategy to fetch repos
            repos = self.api_strategy.fetch_repos(str(installation.id), access_token)

            return repos

        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}")
            raise

    def clone_repository(self, repo_info: GitRepository, user_id: str,
                         org_id: str, upload_key: str, bucket_name: str) -> str:
        """Clone GitLab repository and upload to S3"""
        logger.info(f"Cloning GitLab repository: {repo_info.repo_name}")

        try:
            # Get GAT
            access_token = self._fetch_group_access_token(repo_info.installation_id)

            # Get repository details
            repo_id = repo_info.repo_id
            latest_commit = repo_info.latest_commit.get("id") if repo_info.latest_commit else None

            if not latest_commit:
                logger.warning(f"No commit specified for {repo_info.repo_name}, fetching latest")
                # Fetch latest commit from default branch
                project = self.api_strategy.fetch_project(repo_id, access_token)
                if project:
                    latest_commit = project.get("default_branch", "main")

            # Download repository
            logger.info(f"Downloading repository {repo_id} at commit {latest_commit}")
            zip_content = self.api_strategy.download_repo(repo_id, latest_commit, access_token)

            # Generate metadata
            metadata = generate_codebase_metadata(
                org_id=org_id,
                org_name=org_id,  # Could enhance to fetch actual org name
                repo=repo_info.repo_name,
                repo_id=repo_id,
                owner=repo_info.metadata.get("namespace", {}).get("full_path", ""),
                provider="gitlab",
                commit=latest_commit,
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
        """Handle GitLab webhook events"""
        logger.info(f"Handling GitLab webhook: {event_type} for installation {installation_id}")

        try:
            if event_type == "push":
                return self._handle_push_event(payload, installation_id)
            elif event_type == "merge_request":
                return self._handle_merge_request_event(payload, installation_id)
            elif event_type == "tag_push":
                return self._handle_tag_push_event(payload, installation_id)
            else:
                logger.info(f"Ignoring GitLab event type: {event_type}")
                return {"status": "ignored", "event": event_type}

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            raise

    def revoke_access(self, installation: GitProviderAppInstallation) -> None:
        """Revoke access for a GitLab installation"""
        logger.info(f"Revoking access for GitLab installation {installation.id}")

        # Delete GAT secret
        secret_key = format_secret_name(APP_INSTALL_GAT_NAME_PREFIX, str(installation.id))
        self.secrets_manager.delete_secret(secret_key)
        logger.info(f"Deleted GAT secret for installation {installation.id}")


    # Private helper methods

    def _fetch_group_access_token(self, install_id: str) -> str:
        """Fetch Group Access Token from secrets"""
        secret_key = format_secret_name(APP_INSTALL_GAT_NAME_PREFIX, install_id)
        secret_value = self.secrets_manager.read_secret(secret_key)

        if not secret_value:
            raise ValueError(f"GAT not found for installation: {install_id}")

        return secret_value["token"]

    def _handle_push_event(self, payload: Dict, installation_id: str) -> Dict:
        """Handle push webhook event"""
        project = payload.get("project", {})
        commits = payload.get("commits", [])
        ref = payload.get("ref", "")

        logger.info(f"Push event for project {project.get('name')} with {len(commits)} commits")

        # Extract branch name from ref
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref

        return {
            "status": "processed",
            "event": "push",
            "project": project.get("name"),
            "branch": branch,
            "commits": len(commits)
        }

    def _handle_merge_request_event(self, payload: Dict, installation_id: str) -> Dict:
        """Handle merge request webhook event"""
        merge_request = payload.get("merge_request", {})
        action = payload.get("object_attributes", {}).get("action")

        logger.info(f"Merge request event: {action} for MR {merge_request.get('iid')}")

        return {
            "status": "processed",
            "event": "merge_request",
            "action": action,
            "merge_request_id": merge_request.get("iid")
        }

    def _handle_tag_push_event(self, payload: Dict, installation_id: str) -> Dict:
        """Handle tag push webhook event"""
        project = payload.get("project", {})
        ref = payload.get("ref", "")

        # Extract tag name from ref
        tag = ref.replace("refs/tags/", "") if ref.startswith("refs/tags/") else ref

        logger.info(f"Tag push event for project {project.get('name')}: {tag}")

        return {
            "status": "processed",
            "event": "tag_push",
            "project": project.get("name"),
            "tag": tag
        }


