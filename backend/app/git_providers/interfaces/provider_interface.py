from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.schemas.git_provider_schema import GitRepository
from database.models import GitProviderApp, GitProviderAppInstallation
from shared.interfaces.aws_client_config import AWSClientConfig
from sqlmodel import Session


@dataclass
class WebhookConfig:
    """Generic webhook configuration"""

    callback_url: str
    triggers: list[str]  # Provider-specific event names
    secret_token: str | None = None  # If None, use stored secret
    custom_headers: dict[str, str] | None = None
    ssl_verification: bool = True
    description: str | None = None


@dataclass
class WebhookEventContext:
    app_id: str
    installation_id: str
    organization_id: str
    session: Session


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

    def update_secrets(
        self, installation: GitProviderAppInstallation, token_data: dict
    ) -> None:
        """Update access token while preserving other secrets like webhook tokens

        Args:
            installation: The installation record
            token_data: Provider-specific token data containing new access token

        Note: Default implementation calls store_secrets for backward compatibility.
              Providers should override this to preserve webhook secrets.
        """
        self.store_secrets(installation, token_data)

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
        self,
        installation: GitProviderAppInstallation,
        page_size: int = 100,
        max_pages: int | None = None,
        auto_paginate: bool = True,
    ) -> list[GitRepository]:
        """Fetch repositories accessible by this installation

        Args:
            installation: The installation record
            page_size: Number of repositories to fetch per API call
            max_pages: Maximum number of pages to fetch (None for no limit)
            auto_paginate: Whether to automatically fetch all pages until max_pages or no more pages

        Returns:
            List of GitRepository objects
        """

    @abstractmethod
    def handle_webhook_event(
        self, headers: dict, payload: dict, webhook_event_ctx: WebhookEventContext
    ) -> dict:
        """Handle incoming webhook events

        Args:
            headers: HTTP headers from the webhook request
            payload: JSON payload from the webhook request
            webhook_event_ctx: Context containing app_id, installation_id, organization_id
        """

    @abstractmethod
    def revoke_access(self, installation: GitProviderAppInstallation) -> None:
        """Revoke access for an installation

        Args:
            installation: The installation to revoke
        """

    @abstractmethod
    def register_webhook(
        self,
        installation: GitProviderAppInstallation,
        config: WebhookConfig,
        scope: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Register a webhook for the installation

        Args:
            installation: The installation to register webhook for
            config: Webhook configuration including URL, triggers, headers, etc.
            scope: Optional scope for webhook (e.g., {"type": "repository", "slug": "repo-name"})
                   None for workspace/group level webhooks

        Returns:
            Dict containing webhook details (id, url, active, created_at, etc.)
        """
