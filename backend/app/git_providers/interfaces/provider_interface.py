from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.git_provider_schema import GitRepository
from database.models_v1 import GitProviderApp, GitProviderAppInstallation
from shared.interfaces.aws_client_config import AWSClientConfig


@dataclass
class GitProviderCapabilities:
    """Actual capabilities of a git provider implementation"""

    # Authentication
    supports_oauth_flow: bool = False
    supports_group_access_token: bool = False  # GitLab GAT
    supports_workspace_access_token: bool = False  # Bitbucket WAT
    supports_project_access_token: bool = False  # Bitbucket Project token
    supports_repository_access_token: bool = False  # Bitbucket Repo token
    supports_personal_access_token: bool = False

    # Repository operations
    can_list_repositories: bool = True
    can_clone_repository: bool = True
    can_get_latest_commit: bool = True
    can_create_pull_request: bool = False  # Not in provider interface

    # Webhook support
    supports_webhooks: bool = True
    handles_push_events: bool = True
    handles_merge_request_events: bool = True
    handles_tag_events: bool = True
    handles_fork_events: bool = False

    # Access control
    supports_granular_permissions: bool = False  # Both use org-wide tokens
    supports_multiple_installations: bool = True

    # API features
    supports_pagination: bool = False
    max_repos_per_fetch: int = 100
    uses_git_clone: bool = False  # vs API download

    # Provider info
    api_version: str = "v1"


class GitProviderInterface(ABC):
    """Abstract interface that all Git providers must implement"""

    @classmethod
    @abstractmethod
    def from_config(
        cls, app: GitProviderApp, aws_config: AWSClientConfig
    ) -> "GitProviderInterface":
        """Factory method to create provider instance from app configuration

        Args:
            app: Git provider app configuration
            aws_config: AWS configuration

        Returns:
            Provider instance
        """

    @abstractmethod
    def validate_access_token(self, token_data: dict) -> tuple[bool, str | None]:
        """Validate an access token before installation

        Args:
            token_data: Provider-specific token data

        Returns:
            Tuple of (is_valid, error_message)
        """

    @abstractmethod
    def create_installation(
        self, organization_id: str, app_id: str, token_data: dict
    ) -> GitProviderAppInstallation:
        """Create an installation record

        Args:
            organization_id: Organization ID
            app_id: Git provider app ID
            token_data: Provider-specific token data

        Returns:
            GitProviderAppInstallation instance (not yet persisted)
        """

    @abstractmethod
    def store_secrets(
        self, installation: GitProviderAppInstallation, token_data: dict
    ) -> None:
        """Store access token and related secrets

        Args:
            installation: The installation record
            token_data: Provider-specific token data
        """

    @abstractmethod
    def fetch_secrets(self, installation: GitProviderAppInstallation) -> dict:
        """Fetch stored secrets for an installation
        Args:
            installation: The installation record
        Returns:
            Dictionary of secrets (e.g., access token)
        """

    @abstractmethod
    def fetch_repositories(
        self, installation: GitProviderAppInstallation
    ) -> list[GitRepository]:
        """Fetch repositories accessible by this installation

        Args:
            installation: The installation record

        Returns:
            List of GitRepository objects
        """

    @abstractmethod
    def clone_repository(
        self,
        repo_info: GitRepository,
        user_id: str,
        org_id: str,
        upload_key: str,
        bucket_name: str,
    ) -> str:
        """Clone a repository and upload to S3

        Args:
            repo_info: Repository information
            user_id: User ID initiating the clone
            org_id: Organization ID
            upload_key: S3 upload key
            bucket_name: S3 bucket name

        Returns:
            Presigned download URL
        """

    @abstractmethod
    def handle_webhook(
        self, event_type: str, payload: dict, installation_id: str
    ) -> dict:
        """Handle webhook events

        Args:
            event_type: Provider-specific event type
            payload: Webhook payload
            installation_id: Installation that received the webhook

        Returns:
            Response data
        """

    @abstractmethod
    def revoke_access(self, installation: GitProviderAppInstallation) -> None:
        """Revoke access for an installation

        Args:
            installation: The installation to revoke
        """

    @property
    @abstractmethod
    def capabilities(self) -> GitProviderCapabilities:
        """Get provider capabilities

        Returns:
            GitProviderCapabilities instance describing what this provider supports
        """
