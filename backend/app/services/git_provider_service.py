import logging
from typing import List, Dict, Optional, Type
from sqlmodel import Session

from app.core.config import settings
from app.git_providers.interfaces.provider_interface import GitProviderInterface
from app.git_providers.interfaces.token_types import AccessTokenData, TokenType
from app.git_providers.providers.gitlab_provider2 import GitLabProvider
from app.git_providers.providers.bitbucket_provider import BitbucketProvider
from app.git_providers.utils.errors import GitProviderAccessTokenError, GitProviderAppRevokeError
from app.repositories.git_provider_repository import *
from app.schemas.git_provider_schema import GitRepository, WebhookInfo
from database.models_v1 import GitProviderApp, GitProviderKind, GitProviderAppInstallation
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import AWSSecretManagementStrategy

logger = logging.getLogger(__name__)


class GitProviderService:
    """Unified service for all Git provider operations"""

    # Provider registry
    PROVIDERS: Dict[GitProviderKind, Type[GitProviderInterface]] = {
        GitProviderKind.GITLAB_ENTERPRISE_SELF_MANAGED: GitLabProvider,
        GitProviderKind.BITBUCKET: BitbucketProvider,
    }

    def __init__(self, aws_config: AWSClientConfig):
        self.aws_config = aws_config
        self.secrets_manager = AWSSecretManagementStrategy(aws_config)

    def get_provider(self, app: GitProviderApp) -> GitProviderInterface:
        """Get provider instance for a git provider app"""
        provider_class = self.PROVIDERS.get(app.provider_kind)
        if not provider_class:
            raise ValueError(f"Unsupported provider kind: {app.provider_kind}")

        return provider_class.from_config(app, self.aws_config)

    # App Management
    # ✅
    def create_app(self, session: Session, app_data: Dict) -> GitProviderApp:
        """Create a new git provider app"""
        app = GitProviderApp(**app_data)
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

    def list_apps(self, session: Session, organization_id: str,
                  provider_kind: Optional[GitProviderKind] = None) -> List[GitProviderApp]:
        """List git provider apps for an organization"""
        apps = git_provider_apps_by_org_id(session, organization_id)

        if provider_kind:
            apps = [app for app in apps if app.provider_kind == provider_kind]

        return apps

    def list_app_installations(self, session: Session, organization_id: str,app_id: str) -> List[GitProviderAppInstallation]:
        """List git provider apps for an organization"""
        return git_provider_app_installation_by_org_id(session, organization_id, app_id)

    def delete_app(self, session: Session, organization_id: str, app_id: str) -> None:
        """Delete a git provider app and all installations"""
        app = git_provider_app_by_id(session, organization_id, app_id)
        provider = self.get_provider(app)

        # Delete all installations
        installations = git_provider_app_installation_by_org_id(session, organization_id, app_id)
        for installation in installations:
            provider.revoke_access(installation)
            session.delete(installation)

        # Delete app
        session.delete(app)
        session.commit()
        logger.info(f"Deleted app {app_id} and {len(installations)} installations")

    # Access Token Management

    def install_access_token(self, session: Session, organization_id: str,
                             app_id: str, token_data: Dict) -> GitProviderAppInstallation:
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
            installation = provider.create_installation(organization_id, app_id, token_data)

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

    def update_access_token(self, session: Session, organization_id: str,
                            app_id: str, installation_id: str,
                            token_data: Dict) -> GitProviderAppInstallation:
        """Update an existing access token"""
        try:
            # Get installation and provider
            installation = git_provider_app_installation_by_id(session, installation_id)
            if not installation or installation.organization_id != organization_id or str(installation.git_provider_app_id) != app_id:
                raise ValueError("Installation not found or doesn't match app")

            # app = git_provider_app_by_id(session, organization_id, app_id)
            provider = self.get_provider(installation.git_provider_app)

            # Validate new token
            is_valid, error = provider.validate_access_token(token_data)
            if not is_valid:
                raise GitProviderAccessTokenError(error or "Invalid access token")

            # Update secrets
            provider.store_secrets(installation, token_data)

            logger.info(f"Updated access token for installation {installation_id}")
            return installation

        except Exception as e:
            logger.error(f"Failed to update access token: {e}")
            raise

    def revoke_access_token(self, session: Session, organization_id: str,
                            app_id: str, installation_id: str) -> None:
        """Revoke an access token installation"""
        try:
            # Get installation and provider
            installation = git_provider_app_installation_by_id(session, installation_id)
            if not installation or installation.organization_id != organization_id or str(installation.git_provider_app_id) != app_id:
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

    def list_repositories(self, session: Session, organization_id: str,
                          app_id: str, installation_id: str) -> List[GitRepository]:
        """List repositories for an installation"""
        try:
            # Get installation and provider
            installation = git_provider_app_installation_by_id(session, installation_id)
            if not installation or installation.organization_id != organization_id or str(
                    installation.git_provider_app_id) != app_id:
                raise ValueError("Installation not found or doesn't match app")

            provider = self.get_provider(installation.git_provider_app)

            # Fetch repositories
            return provider.fetch_repositories(installation)

        except GitProviderAppRevokeError as e:
            logger.error(f"Access revoked for installation {installation_id}")
            # Handle revocation
            self.handle_access_revoked(session, organization_id, app_id, installation_id)
            raise
        except Exception as e:
            logger.error(f"Failed to list repositories: {e}")
            raise

    def clone_repository(self, session: Session, organization_id: str,
                         user_id: str, app_id: str, repo_info: GitRepository,
                         upload_key: str, bucket_name: str) -> str:
        """Clone a repository and upload to S3"""
        try:
            # Get app and provider
            app = git_provider_app_by_id(session, organization_id, app_id)
            provider = self.get_provider(app)

            # Clone repository
            download_url = provider.clone_repository(
                repo_info, user_id, organization_id, upload_key, bucket_name
            )

            logger.info(f"Cloned repository {repo_info.repo_name} from {app.provider_kind}")
            return download_url

        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

    # OAuth Operations (GitLab only)

    def authorize_oauth(self, session: Session, organization_id: str,
                        user_id: str, app_id: str) -> str:
        """Generate OAuth authorization URL (GitLab only)"""
        app = git_provider_app_by_id(session, organization_id, app_id)

        if app.provider_kind == GitProviderKind.BITBUCKET:
            raise ValueError("Bitbucket uses Workspace Access Tokens, not OAuth")

        provider = self.get_provider(app)
        return provider.authorize_provider(organization_id, user_id, app_id)

    def handle_oauth_callback(self, session: Session, code: str,
                              state: str) -> None:
        """Handle OAuth callback (GitLab only)"""
        # Decode state to get app info
        import base64
        import json

        state_data = json.loads(base64.b64decode(state))
        app_id = state_data["application_id"]

        app = git_provider_app_by_id(session, state_data["organization_id"], app_id)
        provider = self.get_provider(app)

        provider.handle_app_authorization_callback(code, state_data.get("installation_id"))

    # Webhook Management

    def handle_webhook(self, session: Session, app_id: str, event_type: str,
                       payload: Dict, headers: Dict) -> Dict:
        """Handle webhook events from any provider"""
        # Determine provider from app
        app = session.get(GitProviderApp, app_id)
        if not app:
            raise ValueError(f"App not found: {app_id}")

        provider = self.get_provider(app)

        # Find installation based on provider-specific logic
        installation_id = self._extract_installation_id(app.provider_kind, payload, headers)

        if not installation_id:
            raise ValueError("Cannot determine installation from webhook")

        # Verify webhook signature/secret
        installation = git_provider_app_installation_by_id(session, installation_id)
        if not installation:
            raise ValueError(f"Installation not found: {installation_id}")

        # Handle webhook
        return provider.handle_webhook(event_type, payload, installation_id)

    def get_webhook_info(self, session: Session, organization_id: str,
                         app_id: str, installation_id: str) -> WebhookInfo:
        """Get webhook configuration info"""

        installation = git_provider_app_installation_by_id(session, installation_id)
        if not installation or installation.organization_id != organization_id or str(
                installation.git_provider_app_id) != str(app_id):
            raise ValueError("Installation not found or doesn't match app")

        provider = self.get_provider(installation.git_provider_app)
        secret = provider.fetch_secrets(installation)
        #TODO: move this to provider interface
        webhook_info = WebhookInfo(
            callback_url=f"{settings.AUTH0_AUDIENCE}/git-provider/app/webhook",
            custom_headers={"x-driver-token": installation_id},
            secret_token=secret["secret_token"],
            ssl_verification=True,
            triggers=["push events", "Project or group access token events"],
        )
        return webhook_info

    # Helper Methods

    def _extract_installation_id(self, provider_kind: GitProviderKind,
                                 payload: Dict, headers: Dict) -> Optional[str]:
        """Extract installation ID from webhook payload/headers"""
        if provider_kind == GitProviderKind.GITLAB_ENTERPRISE_SELF_MANAGED:
            return headers.get("x-installation-id")
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

        return None

    def handle_access_revoked(self, session: Session, organization_id: str,
                              app_id: str, installation_id: str) -> None:
        """Handle access revocation"""
        logger.info(f"Handling access revocation for installation {installation_id}")

        try:
            self.revoke_access_token(session, organization_id, app_id, installation_id)
        except Exception as e:
            logger.error(f"Error during revocation cleanup: {e}")


# Create a singleton instance
_service_instance = None


def get_git_provider_service(aws_config: AWSClientConfig) -> GitProviderService:
    """Get or create the GitProviderService singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = GitProviderService(aws_config)
    return _service_instance