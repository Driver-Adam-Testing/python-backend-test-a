from abc import ABC, abstractmethod, abstractclassmethod
from typing import List, Dict, Optional, Tuple, Type
from app.schemas.git_provider_schema import GitRepository
from database.models_v1 import GitProviderAppInstallation, GitProviderApp
from shared.interfaces.aws_client_config import AWSClientConfig


class GitProviderInterface(ABC):
    """Abstract interface that all Git providers must implement"""

    @classmethod
    @abstractmethod
    def from_config(cls, app: GitProviderApp, aws_config: AWSClientConfig) -> 'GitProviderInterface':
        """Factory method to create provider instance from app configuration

        Args:
            app: Git provider app configuration
            aws_config: AWS configuration

        Returns:
            Provider instance
        """
        pass

    @abstractmethod
    def validate_access_token(self, token_data: dict) -> tuple[bool, str|None]:
        """Validate an access token before installation

        Args:
            token_data: Provider-specific token data

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def create_installation(self, organization_id: str, app_id: str,
                            token_data: dict) -> GitProviderAppInstallation:
        """Create an installation record

        Args:
            organization_id: Organization ID
            app_id: Git provider app ID
            token_data: Provider-specific token data

        Returns:
            GitProviderAppInstallation instance (not yet persisted)
        """
        pass

    @abstractmethod
    def store_secrets(self, installation: GitProviderAppInstallation,
                      token_data: dict) -> None:
        """Store access token and related secrets

        Args:
            installation: The installation record
            token_data: Provider-specific token data
        """
        pass

    @abstractmethod
    def fetch_secrets(self, installation: GitProviderAppInstallation) -> dict:
        """Fetch stored secrets for an installation
        Args:
            installation: The installation record
        Returns:
            Dictionary of secrets (e.g., access token)
        """
        pass

    @abstractmethod
    def fetch_repositories(self, installation: GitProviderAppInstallation) -> List[GitRepository]:
        """Fetch repositories accessible by this installation

        Args:
            installation: The installation record

        Returns:
            List of GitRepository objects
        """
        pass

    @abstractmethod
    def clone_repository(self, repo_info: GitRepository, user_id: str,
                         org_id: str, upload_key: str, bucket_name: str) -> str:
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
        pass

    @abstractmethod
    def handle_webhook(self, event_type: str, payload: dict,
                       installation_id: str) -> dict:
        """Handle webhook events

        Args:
            event_type: Provider-specific event type
            payload: Webhook payload
            installation_id: Installation that received the webhook

        Returns:
            Response data
        """
        pass

    @abstractmethod
    def revoke_access(self, installation: GitProviderAppInstallation) -> None:
        """Revoke access for an installation

        Args:
            installation: The installation to revoke
        """
        pass