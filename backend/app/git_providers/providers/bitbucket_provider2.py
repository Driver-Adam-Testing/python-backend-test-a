import json
import logging
from enum import Enum
from typing import Any

import modal
from app.core.config import settings
from app.git_providers.core.config import GitProviderConfig
from app.git_providers.interfaces.provider_interface import (
    GitProviderCapabilities,
    GitProviderInterface,
    WebhookConfig,
    WebhookEventContext,
)
from app.git_providers.interfaces.token_types import AccessTokenData, TokenType
from app.git_providers.resources.bitbucket_api_resources import BitbucketAPIResources
from app.schemas.git_provider_schema import GitProviderAppTokenSecret, GitRepository
from app.schemas.secret_management_schema import APP_INSTALL_WAT_NAME_PREFIX
from database.models_v1 import GitProviderApp, GitProviderAppInstallation
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)

logger = logging.getLogger(__name__)


class BitbucketTokenType(str, Enum):
    """Bitbucket-specific token types"""

    WORKSPACE = "workspace_access_token"
    PROJECT = "project_access_token"
    REPOSITORY = "repository_access_token"


class BitbucketProvider(GitProviderInterface):
    """Bitbucket provider implementation supporting multiple access token types"""

    def __init__(
        self, config: GitProviderConfig, secrets_manager: AWSSecretManagementStrategy
    ):
        self.config = config
        self.secrets_manager = secrets_manager
        self.api_strategy = BitbucketAPIResources(config.base_url)

    @classmethod
    def from_config(
        cls, app: GitProviderApp, aws_config: AWSClientConfig
    ) -> "BitbucketProvider":
        """Create BitbucketProvider from app configuration"""
        from app.git_providers.core.config_loader import load_provider_config

        secrets_manager = AWSSecretManagementStrategy(aws_config)
        config = load_provider_config(app, client_secret=None)

        return cls(config, secrets_manager)

    @property
    def capabilities(self) -> GitProviderCapabilities:
        """Get Bitbucket provider capabilities"""
        return GitProviderCapabilities(
            # Authentication
            supports_oauth_flow=False,
            supports_group_access_token=False,
            supports_workspace_access_token=True,
            supports_project_access_token=True,
            supports_repository_access_token=True,
            supports_personal_access_token=False,
            # Repository operations
            can_list_repositories=True,
            can_clone_repository=True,
            can_get_latest_commit=True,
            can_create_pull_request=False,  # Not in provider interface
            # Webhook support
            supports_webhooks=True,
            can_register_webhooks=True,  # Bitbucket supports webhook registration
            handles_push_events=True,
            handles_merge_request_events=False,  # Uses pull request events instead
            handles_tag_events=False,
            handles_fork_events=True,
            # Access control
            supports_granular_permissions=True,  # Project/repo tokens provide granular access
            supports_multiple_installations=True,
            # API features
            supports_pagination=True,  # Implemented in list_repositories
            max_repos_per_fetch=100,
            uses_git_clone=True,  # Uses actual git clone
            # Provider info
            api_version="2.0",  # Bitbucket API v2
        )

    def validate_access_token(self, token_data: dict) -> tuple[bool, str | None]:
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
                workspace_name, access_token.token
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

    def create_installation(
        self, organization_id: str, app_id: str, token_data: dict
    ) -> GitProviderAppInstallation:
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
            misc_metadata=metadata,
        )

    def store_secrets(
        self, installation: GitProviderAppInstallation, token_data: dict
    ) -> None:
        """Store Bitbucket Access Token in AWS Secrets Manager"""
        access_token = AccessTokenData(**token_data)

        # Generate webhook secret
        import secrets

        webhook_secret = secrets.token_urlsafe(32)

        secret_key = format_secret_name(
            APP_INSTALL_WAT_NAME_PREFIX, str(installation.id)
        )
        secret_value = json.dumps(
            GitProviderAppTokenSecret(
                token=access_token.token, secret_token=webhook_secret
            ).model_dump()
        )

        self.secrets_manager.write_secret(secret_key, secret_value)
        logger.info(f"Stored WAT for Bitbucket installation {installation.id}")

    def fetch_secrets(self, installation: GitProviderAppInstallation) -> dict:
        """Fetch stored secrets for a Bitbucket installation"""
        secret_key = format_secret_name(
            APP_INSTALL_WAT_NAME_PREFIX, str(installation.id)
        )
        secret_value = self.secrets_manager.read_secret(secret_key)

        if not secret_value:
            raise ValueError(
                f"Access token not found for installation: {installation.id}"
            )

        return secret_value

    def fetch_repositories(
        self, installation: GitProviderAppInstallation
    ) -> list[GitRepository]:
        """Fetch Bitbucket repositories based on token type"""
        logger.info(f"Fetching repositories for installation: {installation.id}")

        try:
            # Get token and metadata from secrets
            secrets = self.fetch_secrets(installation)
            access_token = secrets["token"]
            workspace = installation.git_provider_app.name
            repos_data = self.api_strategy.list_repositories(workspace, access_token)
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
                    logger.warning(
                        f"Failed to fetch latest commit for {repo['name']}: {e}"
                    )

                repos.append(
                    GitRepository(
                        provider_name=str(installation.git_provider_app.provider_kind),
                        provider_kind=installation.git_provider_app.provider_kind,
                        org=repo["workspace"]["name"],
                        installation_id=str(installation.id),
                        repo_name=repo["name"],
                        last_updated=repo.get("updated_on"),
                        default_branch=repo["mainbranch"]["name"],  #
                        latest_commit=latest_commit,
                        metadata={
                            "id": repo["uuid"],  # Store repo ID in metadata
                            "workspace": repo["workspace"]["name"],
                            "slug": repo["slug"],
                            "project_key": repo.get("project", {}).get("key"),
                            "project_name": repo.get("project", {}).get("name"),
                            "is_private": repo.get("is_private", True),
                            "language": repo.get("language"),
                            "created_on": repo.get("created_on"),
                            "updated_on": repo.get("updated_on"),
                            "full_name": repo["full_name"],
                            "links": repo.get("links", {}),
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

    # https://support.atlassian.com/bitbucket-cloud/docs/manage-webhooks/
    def handle_webhook_event(
        self, headers: dict, payload: dict, webhook_event_ctx: WebhookEventContext
    ) -> dict:
        """Handle Bitbucket webhook events"""
        installation_id = webhook_event_ctx.installation_id

        event_type = headers["x-event-key"]
        hook_id = headers["x-hook-uuid"]
        logger.info(
            f"Handling Bitbucket webhook: {event_type} for installation {installation_id}"
        )

        # Bitbucket event types are prefixed (e.g., "repo:push")
        if event_type == "repo:push":
            return self._handle_push_event(payload, webhook_event_ctx)
        elif event_type == "pullrequest:created" or event_type == "pullrequest:updated":
            # TODO: Handle pull request events
            return self._handle_pull_request_event()
        else:
            logger.info(f"Ignoring Bitbucket event type: {event_type}")
        return {"message": "Event ignored"}

    def revoke_access(self, installation: GitProviderAppInstallation) -> None:
        """Revoke access for a Bitbucket installation"""
        logger.info(f"Revoking access for Bitbucket installation {installation.id}")

        # Delete access token secret
        secret_key = format_secret_name(
            APP_INSTALL_WAT_NAME_PREFIX, str(installation.id)
        )
        self.secrets_manager.delete_secret(secret_key)
        logger.info(f"Deleted access token secret for installation {installation.id}")

    def register_webhook(
        self,
        installation: GitProviderAppInstallation,
        config: WebhookConfig,
        scope: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Register a Bitbucket webhook with installation ID as query param"""
        logger.info(f"Registering webhook for Bitbucket installation {installation.id}")

        try:
            # Add installation_id as query parameter
            callback_url = config.callback_url
            separator = "&" if "?" in callback_url else "?"
            callback_url = f"{callback_url}{separator}installation_id={installation.id}"

            # Use stored or provided secret token
            secrets = self.fetch_secrets(installation)
            secret_token = config.secret_token or secrets.get("secret_token")

            # Map triggers to Bitbucket events
            bitbucket_events = self._map_triggers_to_events(config.triggers)

            # Get access token
            access_token = secrets["token"]

            # Create webhook configuration
            webhook_config = {
                "url": callback_url,
                "events": bitbucket_events,
                "secret": secret_token,
                "active": True,
                "description": config.description or "DriverAI Webhook",
            }

            # Create webhook based on scope
            if scope and scope.get("type") == "repository":
                webhook_data = self.api_strategy.create_repository_webhook(
                    workspace=installation.git_provider_app.name,
                    repo_slug=scope["slug"],
                    config=webhook_config,
                    access_token=access_token,
                )
            else:
                # Workspace-level webhook
                webhook_data = self.api_strategy.create_workspace_webhook(
                    workspace=installation.git_provider_app.name,
                    config=webhook_config,
                    access_token=access_token,
                )

            # Store webhook metadata
            self._store_webhook_metadata(
                installation,
                {
                    "webhook_id": webhook_data["uuid"],
                    "callback_url": callback_url,
                    "custom_headers": config.custom_headers,  # Stored for reference
                    "ssl_verification": config.ssl_verification,
                    "scope": scope,
                },
            )

            logger.info(
                f"Successfully registered webhook {webhook_data['uuid']} for installation {installation.id}"
            )

            return {
                "id": webhook_data["uuid"],
                "callback_url": callback_url,
                "triggers": config.triggers,
                "active": webhook_data["active"],
                "created_at": webhook_data.get("created_at"),
                "provider_specific": webhook_data,
            }

        except Exception as e:
            logger.error(f"Failed to register webhook: {e}")
            raise

    def fetch_secrets_by_id(self, installation_id: str) -> dict:
        """Fetch secrets by installation ID"""
        secret_key = format_secret_name(APP_INSTALL_WAT_NAME_PREFIX, installation_id)
        secret_value = self.secrets_manager.read_secret(secret_key)

        if not secret_value:
            raise ValueError(
                f"Access token not found for installation: {installation_id}"
            )

        # Handle both old format (direct token) and new format (dict)
        if isinstance(secret_value, str):
            # Legacy format - assume workspace token
            return {
                "token": secret_value,
                "token_type": BitbucketTokenType.WORKSPACE.value,
            }

        return secret_value

    # Private helper methods

    def _handle_push_event(
        self, body: dict, webhook_event_ctx: WebhookEventContext
    ) -> dict:
        """Handle Bitbucket push event - moved from routes"""
        installation_id = webhook_event_ctx.installation_id
        organization_id = webhook_event_ctx.organization_id

        push = body.get("push", {})
        repository = body.get("repository", {})
        changes = push.get("changes", [])

        # Extract repository info
        repo_name = repository.get("name")
        repo_id = repository.get("uuid")
        workspace = repository["workspace"]["name"]
        full_name = repository.get("full_name")

        # Process all branch changes
        for change in changes:
            if change.get("new", {}).get("type") == "branch":
                branch_name = change["new"]["name"]
                commit_hash = change["new"]["target"]["hash"]

                # Get default branch from repository
                default_branch = repository.get("mainbranch", {}).get("name", "main")

                if branch_name != default_branch:
                    logger.info(
                        "Push event ignored: Not the default branch. Workspace: %s, Repo: %s, Branch: %s, Install ID: %s",
                        workspace,
                        repo_name,
                        branch_name,
                        installation_id,
                    )
                    continue

                logger.info(
                    "Push event on default branch. Workspace: %s, Repo: %s, Branch: %s, Install ID: %s",
                    workspace,
                    repo_name,
                    branch_name,
                    installation_id,
                )

                repos_pushed = [
                    {
                        "repo_id": repo_id,
                        "repo_name": repo_name,
                        "full_name": full_name,
                        "commit": commit_hash,
                        "metadata": {
                            "workspace": workspace,
                            "slug": repo_name,
                        },
                        "installation_id": installation_id,
                        "latest_commit": {
                            "id": commit_hash,
                        },
                    }
                ]

                handle_bitbucket_events = modal.Function.lookup(
                    "inspector-v2",
                    "handle_bitbucket_events",
                    environment_name=settings.MODAL_ENVIRONMENT,
                )
                handle_bitbucket_events.spawn(
                    installation_id,
                    organization_id,
                    [],
                    [],
                    repos_pushed,
                )

        return {"message": "Push event processed"}

    def _handle_pull_request_event(
        self, payload: dict, webhook_event_ctx: WebhookEventContext
    ) -> dict:
        """Handle pull request webhook event"""
        # TODO: Implement pull request event handling
        # TODO: in push tech docs cancel open pull requests before creating new ones
        return {"message": "Event ignored: pull request events not implemented"}

    def _map_triggers_to_events(self, triggers: list[str]) -> list[str]:
        """Map generic triggers to Bitbucket-specific events"""
        TRIGGER_MAP = {
            "push events": "repo:push",
            "pull request events": ["pullrequest:created", "pullrequest:updated"],
            "merge events": "pullrequest:fulfilled",
            "fork events": "repo:fork",
        }

        events = []
        for trigger in triggers:
            # Use exact match if it's already a Bitbucket event
            if trigger in [
                "repo:push",
                "pullrequest:created",
                "pullrequest:updated",
                "pullrequest:fulfilled",
                "repo:fork",
            ]:
                events.append(trigger)
            else:
                # Map generic trigger
                mapped = TRIGGER_MAP.get(trigger, trigger)
                if isinstance(mapped, list):
                    events.extend(mapped)
                else:
                    events.append(mapped)

        return list(set(events))  # Remove duplicates

    # def _store_webhook_metadata(
    #     self, installation: GitProviderAppInstallation, webhook_info: Dict[str, Any]
    # ) -> None:
    #     """Store webhook metadata in installation"""
    #     from datetime import datetime
    #
    #     metadata = installation.misc_metadata or {}
    #     webhooks = metadata.get("webhooks", [])
    #
    #     webhooks.append(
    #         {
    #             **webhook_info,
    #             "created_at": datetime.utcnow().isoformat(),
    #         }
    #     )
    #
    #     metadata["webhooks"] = webhooks
    #     # Note: In a real implementation, you would update the installation
    #     # record in the database here
    #     logger.info(
    #         f"Stored webhook metadata for installation {installation.id}: {webhook_info['webhook_id']}"
    #     )
