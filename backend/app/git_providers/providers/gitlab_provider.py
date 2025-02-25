import base64
import json
import logging

from app.git_providers.core.config import GitProviderConfig
from app.git_providers.core.config_loader import load_provider_config
from app.git_providers.oauth.gitlab_oauth_strategy import GitLabOAuthStrategy
from app.git_providers.resources.gitlab_resources import GitLabAPIResources
from app.git_providers.utils.errors import GitProviderAppRevokeError
from app.schemas.git_provider_schema import GitRepository
from app.schemas.secret_management_schema import (
    APP_INSTALL_GAT_NAME_PREFIX,
    APP_INSTALL_SECRET_NAME_PREFIX,
    APP_SECRET_NAME_PREFIX,
)
from database.models_v1 import GitProviderApp, GitProviderAppInstallation
from shared.file_storage.aws_s3_client import AWSS3Client, org_id_to_hash
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)

logger = logging.getLogger(__name__)


class GitLabProvider:
    def __init__(
        self: "GitLabProvider",
        config: GitProviderConfig,
        secrets_manager: AWSSecretManagementStrategy,
    ) -> None:
        self.config = config
        self.secrets_manager = secrets_manager
        self.auth_strategy = GitLabOAuthStrategy(config)
        self.api_strategy = GitLabAPIResources(
            self.config.base_url, self.config.provider_kind
        )

    def authorize_provider(
        self, organization_id: str, user_id: str, application_id: str
    ) -> str:
        logger.info(
            f"Authorizing provider for organization {organization_id}, user {user_id}, and application {application_id}"
        )
        state = {
            "organization_id": organization_id,
            "user_id": user_id,
            "application_id": application_id,
        }

        state_str = json.dumps(state)
        state_bytes = base64.b64encode(state_str.encode("utf-8"))
        state_str = state_bytes.decode("utf-8")
        return self.auth_strategy.generate_authorization_url(state=state_str)

    def handle_app_authorization_callback(
        self, code: str, installation_id: str
    ) -> None:
        logger.info(
            f"Handling app authorization callback for installation ID {installation_id}"
        )
        app_install_secret_key = format_secret_name(
            APP_INSTALL_SECRET_NAME_PREFIX, str(installation_id)
        )

        access_token_data = self.auth_strategy.exchange_code_for_token(code)
        app_install_secret_value = json.dumps(access_token_data)

        self.secrets_manager.write_secret(
            app_install_secret_key, app_install_secret_value
        )

    def fetch_access_token(self, install_id: str) -> str:
        logger.info(f"Fetching access token for installation ID {install_id}")
        install_key = format_secret_name(APP_INSTALL_SECRET_NAME_PREFIX, install_id)
        secret_value = self.secrets_manager.read_secret(install_key)
        if not secret_value:
            raise ValueError("Access token not found")

        access_token, refresh_token = (
            secret_value["access_token"],
            secret_value["refresh_token"],
        )

        if not self.auth_strategy.is_token_valid(access_token):
            logger.info("Access token not valid, refreshing")
            new_token = self.auth_strategy.refresh_access_token(refresh_token)
            access_token = new_token["access_token"]
            logger.info("New access token acquired")
            if self.auth_strategy.is_token_valid(access_token):
                logger.info("Writing new access token to secrets manager")
                self.secrets_manager.write_secret(
                    install_key,
                    json.dumps(new_token),
                )
            else:
                logger.error("New access token not valid")
                raise GitProviderAppRevokeError("Access token revoked or expired")

        return access_token

    def fetch_group_access_token(self, install_id: str) -> str:
        logger.info(f"Fetching group access token for installation ID {install_id}")
        install_key = format_secret_name(APP_INSTALL_GAT_NAME_PREFIX, install_id)
        secret_value = self.secrets_manager.read_secret(install_key)
        if not secret_value:
            raise ValueError("Access token not found")

        group_access_token = secret_value["token"]

        return group_access_token

    def fetch_repos(
        self, app_installation: GitProviderAppInstallation
    ) -> list[GitRepository]:
        logger.info(f"Fetching repositories for installation ID {app_installation.id}")
        access_token = self.fetch_access_token(str(app_installation.id))
        return self.api_strategy.fetch_repos(str(app_installation.id), access_token)

    def fetch_group_repos(
        self, app_installation: GitProviderAppInstallation
    ) -> list[GitRepository]:
        logger.info(f"Fetching repositories for installation ID {app_installation.id}")
        access_token = self.fetch_group_access_token(str(app_installation.id))
        return self.api_strategy.fetch_repos(str(app_installation.id), access_token)

    def clone_repository(
        self,
        repo_info: GitRepository,
        user_id: str,
        org_id: str,
        upload_key: str,
        bucket_name: str,
    ) -> str:
        logger.info(
            f"Cloning repository {repo_info.repo_name} for installation ID {repo_info.installation_id}"
        )
        installation_id = repo_info.installation_id
        repo_id = repo_info.metadata["id"]
        access_token = self.fetch_group_access_token(installation_id)

        # find the GAT the repo belongs to
        if not access_token:
            logger.error(
                f"Failed to find access token for repository {repo_info.repo_name}"
            )
            raise ValueError("Failed to find access token for repository")

        latest_commit = repo_info.latest_commit["commit"]["id"]
        logger.info(
            f"Downloading repository {repo_info.repo_name} for installation ID {repo_info.installation_id}"
        )
        zip_content = self.api_strategy.download_repo(
            repo_id, latest_commit, access_token
        )
        logger.info(
            f"Generating codebase metadata for repository {repo_info.repo_name} for installation ID {repo_info.installation_id}"
        )
        # bind the repo_id to the installation_id to make it easy to identify which provider and repo they belong to
        repo_identifier = f"DriverInstallId_{installation_id}:GitLabRepoId_{repo_id!s}"
        metadata = generate_codebase_metadata(
            org_id,
            repo_info.org,
            repo_info.repo_name,
            repo_identifier,
            user_id,
            str(repo_info.provider_kind),
            latest_commit,
            upload_key,
        )
        logger.info(f"Uploading repository {repo_info.repo_name} to S3")
        s3_client = AWSS3Client(self.secrets_manager.config)
        success = s3_client.upload_to_s3(
            zip_content=zip_content,
            metadata=metadata,
            upload_key=upload_key,
            bucket=bucket_name,
        )
        if not success:
            logger.error("Failed to upload to S3")
            raise ValueError("Failed to upload to S3")

        logger.info(
            f"Generating presigned URL for repository {repo_info.repo_name} for installation ID {repo_info.installation_id}"
        )
        analysis_download_url = s3_client.generate_get_presigned_url(
            key=upload_key, bucket=bucket_name
        )
        return analysis_download_url

    @classmethod
    def from_config(
        cls, git_provider_app: GitProviderApp, aws_config: AWSClientConfig
    ) -> "GitLabProvider":
        secrets_manager = AWSSecretManagementStrategy(config=aws_config)
        app_secret_value = secrets_manager.read_secret(
            format_secret_name(APP_SECRET_NAME_PREFIX, str(git_provider_app.id))
        )

        git_provider_cfg = load_provider_config(
            git_provider_app,
            app_secret_value.get("client_secret", None) if app_secret_value else None,
        )

        return cls(git_provider_cfg, secrets_manager)


def generate_codebase_metadata(
    org_id: str,
    org_name: str,
    repo: str,
    repo_id: str,
    owner: str,
    provider: str,
    commit: str,
    upload_key: str,
) -> dict:
    org_id_hash = org_id_to_hash(org_id)
    return {
        "unhashed_organization_id": org_id,
        "organization_id": org_id_hash,
        "org_bucket": org_id_hash,
        "org_name": org_name,
        "creator_id": owner,
        "file_path": upload_key,
        "codebase_name": repo,
        "content_type": "codebase",
        "provider": provider.lower(),
        "version": commit,
        "repository_id": repo_id,
    }
