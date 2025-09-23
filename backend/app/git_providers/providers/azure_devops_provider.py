import json
import logging
from typing import Any

import modal
from app.core.config import settings
from app.git_providers.core.config import GitProviderConfig
from app.git_providers.core.config_loader import load_provider_config
from app.git_providers.interfaces.provider_interface import (
    GitProviderInterface,
    WebhookConfig,
    WebhookEventContext,
)
from app.git_providers.resources.azure_devops_resources import AzureDevOpsAPIResources
from app.git_providers.utils.vcs_auto_update import is_update_required
from app.schemas.git_provider_schema import (
    GitRepository,
)
from app.schemas.secret_management_schema import (
    APP_INSTALL_PAT_NAME_PREFIX,
)
from database.models import GitProviderApp, GitProviderAppInstallation
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)

logger = logging.getLogger(__name__)


class AzureDevOpsProvider(GitProviderInterface):
    """Azure DevOps provider implementation supporting Personal Access Tokens"""

    def __init__(
        self, config: GitProviderConfig, secrets_manager: AWSSecretManagementStrategy
    ) -> None:
        self.config = config
        self.secrets_manager = secrets_manager
        self.api_strategy = AzureDevOpsAPIResources(
            config.base_url, config.provider_kind
        )

    @classmethod
    def from_config(
        cls, app: GitProviderApp, aws_config: AWSClientConfig
    ) -> "AzureDevOpsProvider":
        """Create provider instance from app configuration"""
        secrets_manager = AWSSecretManagementStrategy(aws_config)
        config = load_provider_config(app, client_secret=None)
        return cls(config, secrets_manager)

    def validate_access_token(
        self, token_data: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Validate Personal Access Token against Azure DevOps API"""
        try:
            # Extract token from token_data
            token = token_data.get("token")
            if not token:
                return False, "No token provided"

            # Validate token by making a request to Azure DevOps profile API
            response = self.api_strategy.validate_token(token)
            if response.get("status") == "success":
                return True, None
            else:
                return False, response.get("error", "Token validation failed")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False, str(e)

    def create_installation(
        self, organization_id: str, app_id: str, token_data: dict[str, Any]
    ) -> GitProviderAppInstallation:
        """Create installation record for Azure DevOps PAT"""
        # Extract organization and project from token_data
        # organization = token_data["metadata"].get("organization"]
        project = token_data["metadata"]["project"]
        metadata = {
            "kind": token_data["token_type"],
            "name": project,
            # "organization": organization,
        }
        return GitProviderAppInstallation(
            git_provider_app_id=app_id,
            organization_id=organization_id,
            misc_metadata=metadata,
        )

    def store_secrets(
        self, installation: GitProviderAppInstallation, token_data: dict[str, Any]
    ) -> None:
        """Store Personal Access Token and related secrets"""
        try:
            # Generate webhook secret
            import secrets

            webhook_secret = secrets.token_urlsafe(32)

            # Store the PAT with webhook secret
            pat_secret_name = format_secret_name(
                APP_INSTALL_PAT_NAME_PREFIX, str(installation.id)
            )
            token = token_data["token"]
            # organization = token_data["metadata"]["organization"]
            project = token_data["metadata"]["project"]
            pat_secret = {
                "token": token,
                # "organization": organization,
                "project": project,
                "secret_token": webhook_secret,
            }
            self.secrets_manager.write_secret(pat_secret_name, json.dumps(pat_secret))

            logger.info(f"Stored Azure DevOps PAT for installation {installation.id}")
        except Exception as e:
            logger.error(f"Failed to store Azure DevOps secrets: {e}")
            raise

    def update_secrets(
        self, installation: GitProviderAppInstallation, token_data: dict[str, Any]
    ) -> None:
        """Update Personal Access Token while preserving webhook secret"""
        try:
            pat_secret_name = format_secret_name(
                APP_INSTALL_PAT_NAME_PREFIX, str(installation.id)
            )

            # Fetch existing secrets to preserve webhook secret
            existing_secrets = self.secrets_manager.read_secret(pat_secret_name)
            if not existing_secrets or "secret_token" not in existing_secrets:
                raise ValueError(
                    f"No existing webhook secret found for installation {installation.id}"
                )

            webhook_secret = existing_secrets["secret_token"]

            # Update only the token, preserve webhook secret
            token = token_data["token"]
            # organization = token_data["metadata"]["organization"]
            project = token_data["metadata"]["project"]
            pat_secret = {
                "token": token,
                # "organization": organization,
                "project": project,
                "secret_token": webhook_secret,
            }
            self.secrets_manager.write_secret(pat_secret_name, json.dumps(pat_secret))

            logger.info(
                f"Updated PAT for Azure DevOps installation {installation.id}, webhook secret preserved"
            )
        except Exception as e:
            logger.error(f"Failed to update Azure DevOps secrets: {e}")
            raise

    def fetch_secrets(self, installation: GitProviderAppInstallation) -> dict[str, Any]:
        """Fetch stored secrets for the installation"""
        pat_secret_name = format_secret_name(
            APP_INSTALL_PAT_NAME_PREFIX, str(installation.id)
        )
        secret_value = self.secrets_manager.read_secret(pat_secret_name)

        if not secret_value:
            raise ValueError(
                f"Access token not found for installation: {installation.id}"
            )

        return secret_value

    def fetch_repositories(
        self, installation: GitProviderAppInstallation
    ) -> list[GitRepository]:
        """Fetch repositories accessible by the installation"""
        logger.info(f"Fetching repositories for installation: {installation.id}")

        try:
            # Get token and metadata from secrets
            secrets = self.fetch_secrets(installation)
            token = secrets["token"]
            organization = secrets.get("organization", "")
            project_name = secrets.get("project", "")

            # Fetch repositories using the API strategy
            repos_data = self.api_strategy.fetch_repositories(token, project_name)

            repos = []
            for repo in repos_data:
                repos.append(
                    GitRepository(
                        provider_name=str(installation.git_provider_app.provider_kind),
                        provider_kind=installation.git_provider_app.provider_kind,
                        org=organization,
                        installation_id=str(installation.id),
                        repo_name=repo["name"],
                        last_updated=repo["project"].get("lastUpdateTime"),
                        default_branch=repo.get("default_branch"),
                        latest_commit=None,
                        metadata={
                            "id": repo["id"],  # Store repo ID in metadata
                            "organization": organization,
                            "project": repo["project"],
                            "default_branch": repo.get("defaultBranch"),
                            "url": repo.get("url"),
                            "created_on": repo.get("creationDate"),
                            "updated_on": repo["project"].get("lastUpdateTime"),
                        },
                    )
                )

            logger.info(
                f"Fetched {len(repos)} repositories for installation {installation.id}"
            )
            return repos

        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}")
            raise

    def handle_webhook_event(
        self,
        headers: dict[str, str],
        payload: dict[str, Any],
        webhook_event_ctx: WebhookEventContext,
    ) -> dict[str, str]:
        """Handle Azure DevOps service hook events"""
        installation_id = webhook_event_ctx.installation_id
        event_type = payload.get("eventType")

        logger.info(
            f"Handling Azure DevOps webhook: {event_type} for installation {installation_id}"
        )
        secret_key = format_secret_name(APP_INSTALL_PAT_NAME_PREFIX, installation_id)
        secret = self.secrets_manager.read_secret(secret_key)

        if not secret.get("secret_token"):
            logger.error(f"Secret not found for installation ID {installation_id}")
            raise PermissionError("Insufficient permissions")

        secret_token = secret["secret_token"]
        if not self._verify_webhook_signature(headers, secret_token):
            logger.error(f"Secret token mismatch for installation ID {installation_id}")
            raise PermissionError("Insufficient permissions")

        try:
            # Extract event information
            resource = payload.get("resource", {})

            if event_type == "git.push":
                return self._handle_push_event(resource, webhook_event_ctx)
            else:
                logger.info(f"Ignoring Azure DevOps event type: {event_type}")
                return {"message": "Event ignored"}

        except Exception as e:
            logger.error(f"Failed to handle Azure DevOps webhook event: {e}")
            return {"status": "error", "message": str(e)}

    def revoke_access(self, installation: GitProviderAppInstallation) -> None:
        """Revoke access for an Azure DevOps installation"""
        logger.info(f"Revoking access for Azure DevOps installation {installation.id}")

        # Delete access token secret
        pat_secret_name = format_secret_name(
            APP_INSTALL_PAT_NAME_PREFIX, str(installation.id)
        )
        self.secrets_manager.delete_secret(pat_secret_name)
        logger.info(f"Deleted access token secret for installation {installation.id}")

    def register_webhook(
        self,
        installation: GitProviderAppInstallation,
        config: WebhookConfig,
        scope: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register webhook for Azure DevOps (handled manually)"""
        # Azure DevOps webhooks are configured manually through the web interface
        # This method provides the webhook configuration information
        return {
            "id": f"azure-devops-{installation.id}",
            "url": config.callback_url,
            "active": True,
            "created_at": "manual_configuration_required",
            "note": "Azure DevOps webhooks must be configured manually through the Azure DevOps web interface",
        }

    def fetch_secrets_by_id(self, installation_id: str) -> dict[str, Any]:
        """Fetch secrets by installation ID"""
        pat_secret_name = format_secret_name(
            APP_INSTALL_PAT_NAME_PREFIX, installation_id
        )
        secret_value = self.secrets_manager.read_secret(pat_secret_name)

        if not secret_value:
            raise ValueError(
                f"Access token not found for installation: {installation_id}"
            )

        return secret_value

    def _verify_webhook_signature(
        self, headers: dict[str, str], webhook_secret: str
    ) -> bool:
        incoming_webhook_secret = headers.get("x-webhook-token")
        return incoming_webhook_secret == webhook_secret

    def _handle_push_event(
        self, resource: dict[str, Any], webhook_event_ctx: WebhookEventContext
    ) -> dict[str, str]:
        """Handle git push events"""
        installation_id = webhook_event_ctx.installation_id
        organization_id = webhook_event_ctx.organization_id

        # Extract repository information from Azure DevOps push event
        repository = resource.get("repository", {})
        ref_updates = resource.get("refUpdates", [])

        if not ref_updates:
            logger.info("No ref updates in Azure DevOps push event")
            return {"message": "No ref updates"}

        # Get repository details
        repo_name = repository.get("name", "unknown")
        repo_id = repository.get("id", "unknown")
        project = repository.get("project", {})
        project_name = project.get("name", "unknown")
        full_name = f"{project_name}/{repo_name}"

        message = {"message": ""}

        # # Get access token for API calls if needed
        # try:
        #     secrets = self.fetch_secrets_by_id(installation_id)
        # except Exception as e:
        #     logger.error(
        #         f"Failed to fetch access token for installation {installation_id}: {e}"
        #     )
        #     return {"message": "Failed to process push event: missing access token"}

        # Get default branch from repository metadata
        default_branch = repository.get("defaultBranch", "main")
        if not default_branch.startswith("refs/heads/"):
            default_branch = f"refs/heads/{default_branch}"
        default_branch_name = default_branch.replace("refs/heads/", "")

        # Process each ref update
        for ref_update in ref_updates:
            ref_name = ref_update.get("name", "")
            new_object_id = ref_update.get("newObjectId", "")

            # Check if this is a branch update (not a tag)
            if not ref_name.startswith("refs/heads/"):
                logger.info(f"Push event ignored: Not a branch update. Ref: {ref_name}")
                continue

            branch_name = ref_name.replace("refs/heads/", "")

            if branch_name != default_branch_name:
                logger.info(
                    "Push event ignored: Not the default branch. Project: %s, Repo: %s, Branch: %s, Install ID: %s",
                    project_name,
                    repo_name,
                    branch_name,
                    installation_id,
                )
                message = {"message": "Push event ignored (not default branch)"}
                continue

            logger.info(
                "Push event on default branch. Project: %s, Repo: %s, Branch: %s, Install ID: %s",
                project_name,
                repo_name,
                branch_name,
                installation_id,
            )

            # Check if update is required
            process_update, message = is_update_required(
                session=webhook_event_ctx.session,
                org_id=organization_id,
                repo_name=repo_name,
            )

            if process_update:
                repos_pushed = [
                    {
                        "repo_id": repo_id,
                        "repo_name": repo_name,
                        "full_name": full_name,
                        "commit": new_object_id,
                        "metadata": {
                            "id": repo_id,
                            "organization": project_name,
                            "project": project_name,
                            "repository_id": repo_id,
                            "default_branch": default_branch_name,
                            "url": repository.get("url", ""),
                        },
                        "installation_id": installation_id,
                        "latest_commit": {
                            "id": new_object_id,
                        },
                    }
                ]

                # Trigger Azure DevOps events processing
                handle_azure_devops_events = modal.Function.lookup(
                    "inspector-v2",
                    "handle_azure_devops_events",
                    environment_name=settings.MODAL_ENVIRONMENT,
                )
                handle_azure_devops_events.spawn(
                    installation_id,
                    organization_id,
                    [],  # repos_added
                    [],  # repos_deleted
                    repos_pushed,
                )

                logger.info(
                    f"Push event processed for repo: {repo_name}. Processing in background job."
                )

        # NOTE: This message will pertain only to the last ref_update processed
        return message

    # Private helper methods

    def _get_default_branch(
        self,
        organization: str,
        project: str,
        repo_name: str,
        access_token: str,
        repository_data: dict[str, Any] | None = None,
    ) -> str:
        """Get default branch name for a repository, fetching from API if needed"""
        # First check if it's in the provided repository data
        if repository_data:
            default_branch = repository_data.get("defaultBranch")
            if default_branch:
                # Azure DevOps returns refs/heads/branch_name format
                if default_branch.startswith("refs/heads/"):
                    return default_branch.replace("refs/heads/", "")
                return default_branch

        # If not, fetch from API
        try:
            repo_data = self.api_strategy.get_repository(
                organization, project, repo_name, access_token
            )
            if repo_data:
                default_branch = repo_data.get("defaultBranch", "main")
                if default_branch.startswith("refs/heads/"):
                    return default_branch.replace("refs/heads/", "")
                return default_branch
        except Exception as e:
            logger.warning(f"Failed to fetch default branch for {repo_name}: {e}")

        # Fallback to 'main'
        return "main"
