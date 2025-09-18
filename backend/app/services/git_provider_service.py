import logging
from typing import ClassVar

from database.models import (
    GitProviderApp,
    GitProviderAppInstallation,
    GitProviderKind,
)
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)
from sqlmodel import Session

from app.core.config import settings
from app.git_providers.interfaces.provider_interface import (
    GitProviderInterface,
    WebhookEventContext,
)
from app.git_providers.providers.azure_devops_provider import AzureDevOpsProvider
from app.git_providers.providers.bitbucket_provider import BitbucketProvider
from app.git_providers.providers.gitlab_provider import GitLabProvider
from app.git_providers.utils.errors import (
    GitProviderAccessTokenError,
    GitProviderAppRevokeError,
)
from app.repositories.git_provider_repository import (
    git_provider_app_by_id,
    git_provider_app_installation_by_id,
    git_provider_app_installation_by_org_id,
    git_provider_apps_by_org_id,
)
from app.schemas.git_provider_schema import GitRepository, WebhookInfo
from app.schemas.secret_management_schema import (
    APP_INSTALL_WAT_NAME_PREFIX,
)

logger = logging.getLogger(__name__)


class GitProviderService:
    """Unified service for all Git provider operations"""

    # Provider registry
    PROVIDERS: ClassVar[dict[GitProviderKind, type[GitProviderInterface]]] = {
        GitProviderKind.GITLAB_ENTERPRISE_SELF_MANAGED: GitLabProvider,
        GitProviderKind.BITBUCKET: BitbucketProvider,
        GitProviderKind.AZURE_DEVOPS_CLOUD: AzureDevOpsProvider,
    }

    def __init__(self, aws_config: AWSClientConfig) -> None:
        self.aws_config = aws_config
        self.secrets_manager = AWSSecretManagementStrategy(aws_config)

    def get_provider(self, app: GitProviderApp) -> GitProviderInterface:
        """Get provider instance for a git provider app"""
        provider_class = self.PROVIDERS.get(app.provider_kind)
        if not provider_class:
            raise ValueError(f"Unsupported provider kind: {app.provider_kind}")

        return provider_class.from_config(app, self.aws_config)

    # def _get_provider_for_installation(self, installation: GitProviderAppInstallation) -> GitProviderInterface:
    #     """Get provider instance for an installation"""
    #     return self.get_provider(installation.git_provider_app)

    # App Management
    # ✅
    def create_app(self, session: Session, app_data: dict) -> GitProviderApp:
        """Create a new git provider app"""
        app = GitProviderApp(**app_data)

        if app.provider_kind in [GitProviderKind.BITBUCKET]:
            # Bitbucket requires a workspace for apps
            app.provider_metadata = {"workspace": app.name}

        session.add(app)

        try:
            session.commit()
            session.refresh(app)
            logger.info(f"Created {app.provider_kind} app: {app.id}")
            return app
        except Exception as e:
            logger.error(f"Failed to create app: {e}")
            session.rollback()
            raise

    def list_apps(
        self,
        session: Session,
        organization_id: str,
        provider_kind: GitProviderKind | None = None,
    ) -> list[GitProviderApp]:
        """List git provider apps for an organization"""
        apps = git_provider_apps_by_org_id(session, organization_id)

        if provider_kind:
            apps = [app for app in apps if app.provider_kind == provider_kind]

        return apps

    def list_app_installations(
        self, session: Session, organization_id: str, app_id: str
    ) -> list[GitProviderAppInstallation]:
        """List git provider apps for an organization"""
        return git_provider_app_installation_by_org_id(session, organization_id, app_id)

    def delete_app(self, session: Session, organization_id: str, app_id: str) -> None:
        """Delete a git provider app and all installations"""
        app = git_provider_app_by_id(session, organization_id, app_id)
        provider = self.get_provider(app)

        # Delete all installations
        installations = git_provider_app_installation_by_org_id(
            session, organization_id, app_id
        )
        for installation in installations:
            provider.revoke_access(installation)
            session.delete(installation)

        # Delete app
        session.delete(app)
        session.commit()
        logger.info(f"Deleted app {app_id} and {len(installations)} installations")

    # Access Token Management

    def install_access_token(
        self, session: Session, organization_id: str, app_id: str, token_data: dict
    ) -> GitProviderAppInstallation:
        """Install any type of access token (GAT, WAT, OAuth)"""
        try:
            # Get app and provider
            app = git_provider_app_by_id(session, organization_id, app_id)
            provider = self.get_provider(app)

            # Validate token
            is_valid, error = provider.validate_access_token(token_data)
            if not is_valid:
                raise GitProviderAccessTokenError(error or "Invalid access token")

            # Create installation
            installation = provider.create_installation(
                organization_id, app_id, token_data
            )

            # Store in database
            app.app_installations.append(installation)
            session.add(installation)
            session.commit()
            session.refresh(installation)

            # Store secrets
            provider.store_secrets(installation, token_data)

            logger.info(f"Installed access token for app {app_id}: {installation.id}")
            return installation

        except Exception as e:
            logger.error(f"Failed to install access token: {e}")
            session.rollback()
            raise

    def update_access_token(
        self,
        session: Session,
        organization_id: str,
        app_id: str,
        installation_id: str,
        token_data: dict,
    ) -> GitProviderAppInstallation:
        """Update an existing access token"""
        try:
            # Get installation and provider
            installation = git_provider_app_installation_by_id(session, installation_id)
            if (
                not installation
                or installation.organization_id != organization_id
                or str(installation.git_provider_app_id) != app_id
            ):
                raise ValueError("Installation not found or doesn't match app")

            # app = git_provider_app_by_id(session, organization_id, app_id)
            provider = self.get_provider(installation.git_provider_app)

            # Validate new token
            is_valid, error = provider.validate_access_token(token_data)
            if not is_valid:
                raise GitProviderAccessTokenError(error or "Invalid access token")

            # Update secrets while preserving webhook secret
            provider.update_secrets(installation, token_data)

            logger.info(f"Updated access token for installation {installation_id}")
            return installation

        except Exception as e:
            logger.error(f"Failed to update access token: {e}")
            raise

    def revoke_access_token(
        self, session: Session, organization_id: str, app_id: str, installation_id: str
    ) -> None:
        """Revoke an access token installation"""
        try:
            # Get installation and provider
            installation = git_provider_app_installation_by_id(session, installation_id)
            if (
                not installation
                or installation.organization_id != organization_id
                or str(installation.git_provider_app_id) != app_id
            ):
                raise ValueError("Installation not found or doesn't match app")

            provider = self.get_provider(installation.git_provider_app)

            # Revoke access
            provider.revoke_access(installation)

            # Delete from database
            session.delete(installation)
            session.commit()

            logger.info(f"Revoked access token for installation {installation_id}")

        except Exception as e:
            logger.error(f"Failed to revoke access token: {e}")
            session.rollback()
            raise

    # Repository Operations

    def list_repositories(
        self, session: Session, organization_id: str, app_id: str, installation_id: str
    ) -> list[GitRepository]:
        """List repositories for an installation"""
        try:
            # Get installation and provider
            installation = git_provider_app_installation_by_id(session, installation_id)
            if (
                not installation
                or installation.organization_id != organization_id
                or str(installation.git_provider_app_id) != app_id
            ):
                raise ValueError("Installation not found or doesn't match app")

            provider = self.get_provider(installation.git_provider_app)

            # Fetch repositories
            return provider.fetch_repositories(installation)

        except GitProviderAppRevokeError:
            logger.error(f"Access revoked for installation {installation_id}")
            # Handle revocation
            self.handle_access_revoked(
                session, organization_id, app_id, installation_id
            )
            raise
        except Exception as e:
            logger.error(f"Failed to list repositories: {e}")
            raise

    def get_webhook_info(
        self, session: Session, organization_id: str, app_id: str, installation_id: str
    ) -> WebhookInfo:
        """Get webhook configuration info"""

        installation = git_provider_app_installation_by_id(session, installation_id)
        if (
            not installation
            or installation.organization_id != organization_id
            or str(installation.git_provider_app_id) != str(app_id)
        ):
            raise ValueError("Installation not found or doesn't match app")

        provider = self.get_provider(installation.git_provider_app)
        secret = provider.fetch_secrets(installation)

        if installation.git_provider_app.provider_kind == GitProviderKind.BITBUCKET:
            # Bitbucket requires a specific webhook structure
            webhook_info = WebhookInfo(
                callback_url=f"{settings.AUTH0_AUDIENCE}/git-provider/app/webhook?installation_id={installation_id}",
                custom_headers={},
                secret_token=secret["secret_token"],
                ssl_verification=True,
                triggers=["push events"],
            )
        elif (
            installation.git_provider_app.provider_kind
            == GitProviderKind.GITLAB_ENTERPRISE_SELF_MANAGED
        ):
            # TODO: move this to provider interface
            webhook_info = WebhookInfo(
                callback_url=f"{settings.AUTH0_AUDIENCE}/git-provider/app/webhook",
                custom_headers={"x-driver-token": installation_id},
                secret_token=secret["secret_token"],
                ssl_verification=True,
                triggers=["push events", "Project or group access token events"],
            )
        elif (
            installation.git_provider_app.provider_kind
            == GitProviderKind.AZURE_DEVOPS_CLOUD
        ):
            # Azure DevOps service hooks (manually configured)
            webhook_info = WebhookInfo(
                callback_url=f"{settings.AUTH0_AUDIENCE}/git-provider/app/webhook",
                custom_headers={
                    "x-driver-token": installation_id,
                    "x-webhook-token": secret.get("secret_token"),
                },
                secret_token="",  # Not used in Azure DevOps
                ssl_verification=True,
                triggers=["git.push"],
            )
        else:
            raise ValueError(
                f"Unsupported provider kind: {installation.git_provider_app.provider_kind}"
            )
        return webhook_info

    # Helper Methods

    def _extract_installation_id(
        self, provider_kind: GitProviderKind, payload: dict, headers: dict
    ) -> str | None:
        """Extract installation ID from webhook payload/headers"""
        if provider_kind == GitProviderKind.GITLAB_ENTERPRISE_SELF_MANAGED:
            return headers.get("x-driver-token")
        elif provider_kind == GitProviderKind.BITBUCKET:
            # Try headers first
            installation_id = headers.get("x-installation-id")
            if installation_id:
                return installation_id

            # Try to infer from workspace
            workspace = payload.get("workspace", {}).get("slug")
            if workspace:
                # Would need to query DB to find installation by workspace
                # This is a simplified version
                return None
        elif provider_kind == GitProviderKind.AZURE_DEVOPS_CLOUD:
            # Azure DevOps service hooks include installation ID in headers
            return headers.get("x-driver-token")

        return None

    def handle_access_revoked(
        self, session: Session, organization_id: str, app_id: str, installation_id: str
    ) -> None:
        """Handle access revocation"""
        logger.info(f"Handling access revocation for installation {installation_id}")

        try:
            self.revoke_access_token(session, organization_id, app_id, installation_id)
        except Exception as e:
            logger.error(f"Error during revocation cleanup: {e}")

    # Webhook Event Handling
    def handle_webhook_event(
        self, session: Session, installation_id: str, headers: dict, body: dict
    ) -> dict:
        """Handle webhook event by routing to appropriate provider"""

        app_install = git_provider_app_installation_by_id(session, installation_id)
        if not app_install:
            logger.error(f"Installation not found for ID {installation_id}")
            raise ValueError("Installation not found")

        git_provider = self.get_provider(app_install.git_provider_app)
        return git_provider.handle_webhook_event(
            headers,
            body,
            WebhookEventContext(
                app_id=str(app_install.git_provider_app_id),
                installation_id=installation_id,
                organization_id=app_install.organization_id,
                session=session,
            ),
        )

    def _handle_bitbucket_webhook(
        self,
        session: Session,
        app_install: GitProviderAppInstallation,
        headers: dict,
        body: dict,
    ) -> dict:
        """Handle Bitbucket webhook with security validation"""
        installation_id = str(app_install.id)
        event_key = headers.get("x-event-key")
        incoming_secret = headers.get("x-hub-signature")
        # webhook_id = headers.get(
        #     "x-hook-uuid"
        # )  # store this during registration to identify the webhook event target

        # For Bitbucket, validate the webhook secret if provided
        secret = self.secrets_manager.read_secret(
            format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, installation_id)
        )
        if (
            secret
            and secret.get("secret_token")
            and incoming_secret
            and secret["secret_token"] != incoming_secret
        ):
            logger.error(
                f"Secret token mismatch for Bitbucket installation ID {installation_id}"
            )
            raise PermissionError("Insufficient permissions")

        # Get provider and handle event
        provider = self.get_provider(app_install.git_provider_app)

        if event_key == "repo:push":
            logger.info("Bitbucket push event")
            return provider.handle_push_event(
                session, str(app_install.git_provider_app_id), installation_id, body
            )

        return {"message": "Event ignored"}


# Create a singleton instance
_service_instance = None


def get_git_provider_service(aws_config: AWSClientConfig) -> GitProviderService:
    """Get or create the GitProviderService singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = GitProviderService(aws_config)
    return _service_instance
