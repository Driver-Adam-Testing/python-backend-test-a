import json
import logging
import secrets
from typing import Any

from app.git_providers.core.config import GitProviderConfig
from app.git_providers.interfaces.provider_interface import (
    GitProviderInterface,
    WebhookConfig,
    WebhookEventContext,
)
from app.git_providers.resources.bitbucket_dc_api_resources import (
    BitbucketDCAPIResources,
)
from app.git_providers.utils.branch_tracking import get_tracked_branch_or_none
from app.git_providers.utils.vcs_auto_update import is_update_required
from app.schemas.git_provider_schema import (
    BitbucketDCTokenData,
    GitRepository,
)
from app.schemas.secret_management_schema import APP_INSTALL_BBDC_HTTP_NAME_PREFIX
from database.models import GitProviderApp, GitProviderAppInstallation
from hatchet_sdk import Hatchet
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.interfaces.hatchet_interfaces import HandleBitbucketDCEventsInput
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)

logger = logging.getLogger(__name__)


class BitbucketDCProvider(GitProviderInterface):
    """Bitbucket Data Center/Server provider implementation.

    Key differences from Bitbucket Cloud:
    - Uses HTTP Access Tokens (not Workspace Access Tokens)
    - API base: {instance}/rest/api/1.0
    - Clone URL requires actual username (not x-token-auth)
    - Push event: repo:refs_changed
    - PR merged event: pr:merged
    - May use self-signed SSL certificates
    """

    def __init__(
        self,
        config: GitProviderConfig,
        secrets_manager: AWSSecretManagementStrategy,
    ) -> None:
        self.config = config
        self.secrets_manager = secrets_manager
        self.api_resources: BitbucketDCAPIResources | None = None

    def _get_api_resources(
        self,
        base_url: str,
        ca_bundle_path: str | None = None,
        disable_ssl_verify: bool = False,
    ) -> BitbucketDCAPIResources:
        """Get or create API resources instance with SSL configuration."""
        return BitbucketDCAPIResources(
            base_url=base_url,
            ca_bundle_path=ca_bundle_path,
            disable_ssl_verify=disable_ssl_verify,
        )

    @classmethod
    def from_config(
        cls, app: GitProviderApp, aws_config: AWSClientConfig
    ) -> "BitbucketDCProvider":
        """Create BitbucketDCProvider from app configuration."""
        from app.git_providers.core.config_loader import load_provider_config

        secrets_manager = AWSSecretManagementStrategy(aws_config)
        config = load_provider_config(app, client_secret=None)

        return cls(config, secrets_manager)

    def validate_access_token(self, token_data: dict) -> tuple[bool, str | None]:
        """Validate Bitbucket DC HTTP Access Token.

        For Project/Repository tokens, we use Bearer auth only (no username needed).

        Args:
            token_data: Dictionary with token. instance_url is optional
                       (will use app config if not provided).

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            token = token_data.get("token")
            if not token:
                return False, "Token is required"

            # Get instance_url from token_data or app config
            instance_url = token_data.get("instance_url") or self.config.base_url
            if not instance_url:
                return False, "Instance URL is required"

            # Get optional SSL settings
            ca_bundle_path = token_data.get("ca_bundle_path")
            disable_ssl_verify = token_data.get("disable_ssl_verify", False)

            api = self._get_api_resources(
                base_url=instance_url,
                ca_bundle_path=ca_bundle_path,
                disable_ssl_verify=disable_ssl_verify,
            )

            # Store instance_url back in token_data for later use
            token_data["instance_url"] = instance_url

            # Validate token using Bearer auth (no username needed)
            is_valid, message = api.validate_token(token)
            return (is_valid, None) if is_valid else (False, message)

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False, str(e)

    def create_installation(
        self, organization_id: str, app_id: str, token_data: dict
    ) -> GitProviderAppInstallation:
        """Create a new installation for Bitbucket DC."""
        dc_token = BitbucketDCTokenData(**token_data)

        metadata = {
            "kind": "bitbucket_dc_http_token",
            "instance_url": dc_token.instance_url,
        }

        return GitProviderAppInstallation(
            git_provider_app_id=app_id,
            organization_id=organization_id,
            misc_metadata=metadata,
        )

    def store_secrets(
        self, installation: GitProviderAppInstallation, token_data: dict
    ) -> None:
        """Store Bitbucket DC credentials in AWS Secrets Manager."""
        dc_token = BitbucketDCTokenData(**token_data)

        # Generate webhook secret
        webhook_secret = secrets.token_urlsafe(32)

        secret_key = format_secret_name(
            APP_INSTALL_BBDC_HTTP_NAME_PREFIX, str(installation.id)
        )

        secret_value = json.dumps(
            {
                "token": dc_token.token,
                "instance_url": dc_token.instance_url,
                "secret_token": webhook_secret,
                "ca_bundle_path": dc_token.ca_bundle_path,
                "disable_ssl_verify": dc_token.disable_ssl_verify,
            }
        )

        self.secrets_manager.write_secret(secret_key, secret_value)
        logger.info(
            f"Stored HTTP Access Token for Bitbucket DC installation {installation.id}"
        )

    def update_secrets(
        self, installation: GitProviderAppInstallation, token_data: dict
    ) -> None:
        """Update Bitbucket DC credentials while preserving webhook secret."""
        dc_token = BitbucketDCTokenData(**token_data)

        secret_key = format_secret_name(
            APP_INSTALL_BBDC_HTTP_NAME_PREFIX, str(installation.id)
        )

        # Fetch existing secrets to preserve webhook secret
        existing_secrets = self.secrets_manager.read_secret(secret_key)
        if not existing_secrets or "secret_token" not in existing_secrets:
            raise ValueError(
                f"No existing webhook secret found for installation {installation.id}"
            )

        webhook_secret = existing_secrets["secret_token"]

        secret_value = json.dumps(
            {
                "token": dc_token.token,
                "instance_url": dc_token.instance_url,
                "secret_token": webhook_secret,
                "ca_bundle_path": dc_token.ca_bundle_path,
                "disable_ssl_verify": dc_token.disable_ssl_verify,
            }
        )

        self.secrets_manager.write_secret(secret_key, secret_value)
        logger.info(
            f"Updated HTTP Access Token for Bitbucket DC installation {installation.id}"
        )

    def fetch_secrets(self, installation: GitProviderAppInstallation) -> dict:
        """Fetch secrets for an installation."""
        secret_key = format_secret_name(
            APP_INSTALL_BBDC_HTTP_NAME_PREFIX, str(installation.id)
        )
        secret_value = self.secrets_manager.read_secret(secret_key)

        if not secret_value:
            raise ValueError(
                f"Access token not found for installation: {installation.id}"
            )

        return secret_value

    def fetch_secrets_by_id(self, installation_id: str) -> dict:
        """Fetch secrets by installation ID."""
        secret_key = format_secret_name(
            APP_INSTALL_BBDC_HTTP_NAME_PREFIX, installation_id
        )
        secret_value = self.secrets_manager.read_secret(secret_key)

        if not secret_value:
            raise ValueError(
                f"Access token not found for installation: {installation_id}"
            )

        return secret_value

    def fetch_repositories(
        self, installation: GitProviderAppInstallation
    ) -> list[GitRepository]:
        """Fetch Bitbucket DC repositories."""
        logger.info(f"Fetching repositories for installation: {installation.id}")

        try:
            secrets = self.fetch_secrets(installation)
            access_token = secrets["token"]
            instance_url = secrets["instance_url"]

            api = self._get_api_resources(
                base_url=instance_url,
                ca_bundle_path=secrets.get("ca_bundle_path"),
                disable_ssl_verify=secrets.get("disable_ssl_verify", False),
            )

            repos_data = api.list_repositories(access_token)
            repos = []

            for repo in repos_data:
                project_key = repo.get("project", {}).get("key")
                repo_slug = repo.get("slug")

                # Get default branch (requires separate API call for DC)
                default_branch = None
                try:
                    default_branch = api.get_default_branch(
                        project_key, repo_slug, access_token
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch default branch for {project_key}/{repo_slug}: {e}"
                    )

                repos.append(
                    GitRepository(
                        provider_name=str(installation.git_provider_app.provider_kind),
                        provider_kind=installation.git_provider_app.provider_kind,
                        org=project_key,
                        installation_id=str(installation.id),
                        repo_name=repo.get("name"),
                        last_updated=None,  # DC doesn't provide this in list response
                        default_branch=default_branch,
                        latest_commit=None,
                        metadata={
                            "id": repo.get("id"),
                            "project_key": project_key,
                            "project_name": repo.get("project", {}).get("name"),
                            "slug": repo_slug,
                            "is_public": repo.get("public", False),
                            "clone_url": repo.get("links", {})
                            .get("clone", [{}])[0]
                            .get("href")
                            if repo.get("links", {}).get("clone")
                            else None,
                            "instance_url": instance_url,
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
        headers: dict,
        payload: dict,
        webhook_event_ctx: WebhookEventContext,
    ) -> dict:
        """Handle Bitbucket DC webhook events.

        Bitbucket DC uses different event keys than Cloud:
        - repo:refs_changed (push)
        - pr:merged (PR merged)
        """
        installation_id = webhook_event_ctx.installation_id

        event_type = headers.get("x-event-key", "")
        logger.info(
            f"Handling Bitbucket DC webhook: {event_type} for installation {installation_id}"
        )

        if event_type == "repo:refs_changed":
            return self._handle_push_event(payload, webhook_event_ctx)
        elif event_type == "pr:merged":
            return self._handle_pr_merged_event(payload, webhook_event_ctx)
        else:
            logger.info(f"Ignoring Bitbucket DC event type: {event_type}")
            return {"message": "Event ignored"}

    def _handle_push_event(
        self, payload: dict, webhook_event_ctx: WebhookEventContext
    ) -> dict:
        """Handle repo:refs_changed event."""
        installation_id = webhook_event_ctx.installation_id
        organization_id = webhook_event_ctx.organization_id

        repository = payload.get("repository", {})
        changes = payload.get("changes", [])

        project_key = repository.get("project", {}).get("key")
        repo_slug = repository.get("slug")
        repo_name = repository.get("name")
        repo_id = repository.get("id")

        # Get access token for API calls
        try:
            secrets = self.fetch_secrets_by_id(installation_id)
            access_token = secrets["token"]
            instance_url = secrets["instance_url"]
        except Exception as e:
            logger.error(
                f"Failed to fetch access token for installation {installation_id}: {e}"
            )
            return {"message": "Failed to process push event: missing access token"}

        api = self._get_api_resources(
            base_url=instance_url,
            ca_bundle_path=secrets.get("ca_bundle_path"),
            disable_ssl_verify=secrets.get("disable_ssl_verify", False),
        )

        # Get tracked branch or default
        tracked_branch = get_tracked_branch_or_none(
            session=webhook_event_ctx.session,
            org_id=organization_id,
            repo_name=repo_name,
        )
        if not tracked_branch:
            try:
                tracked_branch = api.get_default_branch(
                    project_key, repo_slug, access_token
                )
            except Exception:
                tracked_branch = "main"

        message: dict[str, str] = {"message": ""}

        for change in changes:
            ref = change.get("ref", {})
            if ref.get("type") != "BRANCH":
                continue

            branch_name = ref.get("displayId")
            commit_hash = change.get("toHash")

            if branch_name != tracked_branch:
                logger.info(
                    f"Push event ignored: Not tracked branch. Project: {project_key}, "
                    f"Repo: {repo_name}, Branch: {branch_name}, Tracked: {tracked_branch}"
                )
                message = {"message": "Push event ignored (not tracked branch)"}
                continue

            logger.info(
                f"Push event on tracked branch. Project: {project_key}, "
                f"Repo: {repo_name}, Branch: {branch_name}"
            )

            process_update, update_msg = is_update_required(
                session=webhook_event_ctx.session,
                org_id=organization_id,
                repo_name=repo_name,
            )

            if process_update:
                repos_pushed = [
                    {
                        "repo_id": repo_id,
                        "repo_name": repo_name,
                        "project_key": project_key,
                        "repo_slug": repo_slug,
                        "commit": commit_hash,
                        "tracked_branch": tracked_branch,
                        "installation_id": installation_id,
                        "metadata": {
                            "id": repo_id,
                            "project_key": project_key,
                            "slug": repo_slug,
                            "instance_url": instance_url,
                        },
                    }
                ]

                hatchet = Hatchet()
                handle_dc_events_task = hatchet.stubs.task(
                    name="handle-bitbucket-dc-events-workflow",
                    input_validator=HandleBitbucketDCEventsInput,
                )

                handle_dc_events_task.run_no_wait(
                    HandleBitbucketDCEventsInput(
                        installation_id=installation_id,
                        org_id=organization_id,
                        repos_added=[],
                        repos_deleted=[],
                        repos_pushed=repos_pushed,
                    )
                )
                return {"message": "Push event processed"}
            else:
                message = {"message": update_msg}

        return message

    def _handle_pr_merged_event(
        self, payload: dict, webhook_event_ctx: WebhookEventContext
    ) -> dict:
        """Handle pr:merged event.

        When a PR is merged, we treat it like a push to the target branch.
        """
        installation_id = webhook_event_ctx.installation_id
        organization_id = webhook_event_ctx.organization_id

        pull_request = payload.get("pullRequest", {})
        to_ref = pull_request.get("toRef", {})
        repository = to_ref.get("repository", {})

        project_key = repository.get("project", {}).get("key")
        repo_slug = repository.get("slug")
        repo_name = repository.get("name")
        repo_id = repository.get("id")
        target_branch = to_ref.get("displayId")

        # Get the merge commit from properties
        merge_commit = (
            pull_request.get("properties", {}).get("mergeCommit", {}).get("id")
        )

        if not merge_commit:
            logger.warning("PR merged event missing merge commit ID")
            return {"message": "PR merged event ignored: no merge commit"}

        # Get access token
        try:
            secrets = self.fetch_secrets_by_id(installation_id)
            instance_url = secrets["instance_url"]
        except Exception as e:
            logger.error(f"Failed to fetch access token: {e}")
            return {"message": "Failed to process PR merged event"}

        # Check if target branch is the tracked branch
        tracked_branch = get_tracked_branch_or_none(
            session=webhook_event_ctx.session,
            org_id=organization_id,
            repo_name=repo_name,
        )

        if tracked_branch and target_branch != tracked_branch:
            logger.info(f"PR merged to non-tracked branch: {target_branch}")
            return {"message": "PR merged to non-tracked branch"}

        process_update, update_msg = is_update_required(
            session=webhook_event_ctx.session,
            org_id=organization_id,
            repo_name=repo_name,
        )

        if process_update:
            repos_pushed = [
                {
                    "repo_id": repo_id,
                    "repo_name": repo_name,
                    "project_key": project_key,
                    "repo_slug": repo_slug,
                    "commit": merge_commit,
                    "tracked_branch": target_branch,
                    "installation_id": installation_id,
                    "metadata": {
                        "id": repo_id,
                        "project_key": project_key,
                        "slug": repo_slug,
                        "instance_url": instance_url,
                    },
                }
            ]

            hatchet = Hatchet()
            handle_dc_events_task = hatchet.stubs.task(
                name="handle-bitbucket-dc-events-workflow",
                input_validator=HandleBitbucketDCEventsInput,
            )

            handle_dc_events_task.run_no_wait(
                HandleBitbucketDCEventsInput(
                    installation_id=installation_id,
                    org_id=organization_id,
                    repos_added=[],
                    repos_deleted=[],
                    repos_pushed=repos_pushed,
                )
            )
            return {"message": "PR merged event processed"}

        return {"message": update_msg}

    def revoke_access(self, installation: GitProviderAppInstallation) -> None:
        """Revoke access for a Bitbucket DC installation."""
        logger.info(f"Revoking access for Bitbucket DC installation {installation.id}")

        secret_key = format_secret_name(
            APP_INSTALL_BBDC_HTTP_NAME_PREFIX, str(installation.id)
        )
        self.secrets_manager.delete_secret(secret_key)
        logger.info(f"Deleted access token secret for installation {installation.id}")

    def register_webhook(
        self,
        installation: GitProviderAppInstallation,
        config: WebhookConfig,
        scope: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Register a Bitbucket DC webhook.

        Note: Bitbucket DC webhooks are typically configured via the UI,
        but we support API-based registration for automation.
        """
        logger.info(
            f"Registering webhook for Bitbucket DC installation {installation.id}"
        )

        try:
            secrets = self.fetch_secrets(installation)
            access_token = secrets["token"]
            instance_url = secrets["instance_url"]
            secret_token = config.secret_token or secrets.get("secret_token")

            api = self._get_api_resources(
                base_url=instance_url,
                ca_bundle_path=secrets.get("ca_bundle_path"),
                disable_ssl_verify=secrets.get("disable_ssl_verify", False),
            )

            # Add installation_id as query parameter
            callback_url = config.callback_url
            separator = "&" if "?" in callback_url else "?"
            callback_url = f"{callback_url}{separator}installation_id={installation.id}"

            # Map triggers to Bitbucket DC events
            dc_events = self._map_triggers_to_events(config.triggers)

            if not scope or scope.get("type") != "repository":
                raise ValueError("Bitbucket DC webhooks must be scoped to a repository")

            webhook_config = {
                "url": callback_url,
                "events": dc_events,
                "secret": secret_token,
                "active": True,
                "description": config.description or "Driver AI Webhook",
            }

            webhook_data = api.create_repository_webhook(
                project_key=scope["project_key"],
                repo_slug=scope["slug"],
                config=webhook_config,
                access_token=access_token,
            )

            logger.info(
                f"Successfully registered webhook for installation {installation.id}"
            )

            return {
                "id": webhook_data.get("id"),
                "callback_url": callback_url,
                "triggers": config.triggers,
                "active": webhook_data.get("active", True),
                "provider_specific": webhook_data,
            }

        except Exception as e:
            logger.error(f"Failed to register webhook: {e}")
            raise

    def _map_triggers_to_events(self, triggers: list[str]) -> list[str]:
        """Map generic triggers to Bitbucket DC-specific events."""
        TRIGGER_MAP = {
            "push events": "repo:refs_changed",
            "pull request events": ["pr:opened", "pr:modified"],
            "merge events": "pr:merged",
        }

        events = []
        for trigger in triggers:
            # Use exact match if it's already a DC event
            if trigger in [
                "repo:refs_changed",
                "pr:merged",
                "pr:opened",
                "pr:modified",
            ]:
                events.append(trigger)
            else:
                mapped = TRIGGER_MAP.get(trigger, trigger)
                if isinstance(mapped, list):
                    events.extend(mapped)
                else:
                    events.append(mapped)

        return list(set(events))
