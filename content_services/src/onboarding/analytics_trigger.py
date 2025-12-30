"""Analytics trigger helpers for codebase connection.

These functions are responsible for spawning analytics tasks when a
codebase is connected. They support all git providers:
- GitHub
- GitLab (including Enterprise)
- Bitbucket
- Azure DevOps

Manual uploads (provider="manual") are not supported for analytics.
"""
import logging

logger = logging.getLogger(__name__)


# Provider clone URL patterns
_PROVIDER_CLONE_URLS = {
    "github": lambda name, token: f"https://x-access-token:{token}@github.com/{name}.git" if token else f"https://github.com/{name}.git",
    "gitlab": lambda name, token: f"https://oauth2:{token}@gitlab.com/{name}.git" if token else f"https://gitlab.com/{name}.git",
    "gitlab_enterprise": lambda name, token: f"https://oauth2:{token}@gitlab.com/{name}.git" if token else f"https://gitlab.com/{name}.git",
    "gitlab_enterprise_self_managed": lambda name, token: f"https://oauth2:{token}@gitlab.com/{name}.git" if token else f"https://gitlab.com/{name}.git",
    "bitbucket": lambda name, token: f"https://x-token-auth:{token}@bitbucket.org/{name}.git" if token else f"https://bitbucket.org/{name}.git",
    "azure_devops": lambda name, token: f"https://{token}@dev.azure.com/{name}.git" if token else f"https://dev.azure.com/{name}.git",
}


def get_provider_token_fetchers():
    """Get provider token fetch mapping (deferred import to avoid circular imports)."""
    from shared.inspector.onboarding import (
        gh_ops,
        gitlab_ops,
        bitbucket_ops,
        azure_devops_ops,
    )
    return {
        "github": gh_ops.fetch_app_access_token,
        "gitlab": gitlab_ops.fetch_access_token,
        "gitlab_enterprise": gitlab_ops.fetch_access_token,
        "gitlab_enterprise_self_managed": gitlab_ops.fetch_access_token,
        "bitbucket": bitbucket_ops.fetch_access_token,
        "azure_devops": azure_devops_ops.fetch_access_token,
    }


def get_provider_auth_token(provider: str, install_id: str | None) -> str | None:
    """Get access token for any supported git provider.

    Uses existing fetch functions from shared/inspector/onboarding/*.
    No new auth code needed - reuses existing infrastructure.

    Args:
        provider: Git provider name (github, gitlab, bitbucket, azure_devops)
        install_id: Provider app installation ID (from S3 metadata)

    Returns:
        Access token or None if unavailable/unsupported
    """
    from shared.inspector.onboarding.onboard_utils import AccessTokenError

    if not install_id:
        return None

    token_fetchers = get_provider_token_fetchers()
    token_fetcher = token_fetchers.get(provider)
    if not token_fetcher:
        logger.warning(f"No token fetcher for provider: {provider}")
        return None

    try:
        return token_fetcher(install_id)
    except AccessTokenError as e:
        logger.warning(f"Install {install_id} not found for {provider} (may be uninstalled): {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting {provider} token: {e}")
        return None


def build_clone_url(provider: str, codebase_name: str, auth_token: str | None = None) -> str | None:
    """Build clone URL for repository.

    Uses provider-specific URL patterns matching existing infrastructure.

    Returns:
        Clone URL string, or None if provider not supported
    """
    url_builder = _PROVIDER_CLONE_URLS.get(provider)
    if not url_builder:
        return None
    return url_builder(codebase_name, auth_token)


def spawn_analytics_task(
    codebase_id: str,
    organization_id: str,
    codebase_name: str,
    provider: str,
    install_id: str | None = None,
) -> str | None:
    """Spawn analytics task as background Hatchet job.

    Supports all git providers: GitHub, GitLab, Bitbucket, Azure DevOps.
    Manual uploads (provider="manual") are skipped.

    Returns workflow_run_id if spawned successfully, None otherwise.
    Never raises - analytics failure should not block connection.
    """
    # Deferred imports to avoid Hatchet client initialization at module load
    from workflows.analytics_workflow import analytics_task, AnalyticsInput

    # Skip manual uploads - no git provider means no clone URL
    if provider == "manual":
        logger.info(f"Skipping analytics for manual upload: {codebase_name}")
        return None

    try:
        # Get auth token for private repos
        auth_token = get_provider_auth_token(provider, install_id)

        # Build clone URL
        clone_url = build_clone_url(provider, codebase_name, auth_token)
        if not clone_url:
            logger.warning(f"Unsupported provider for analytics: {provider}")
            return None

        # Extract owner/repo from codebase_name
        if "/" in codebase_name:
            parts = codebase_name.rsplit("/", 1)
            repo_owner, repo_name = parts[0], parts[1]
        else:
            repo_owner, repo_name = "", codebase_name

        analytics_input = AnalyticsInput(
            codebase_id=codebase_id,
            organization_id=organization_id,
            clone_url=clone_url,
            repo_owner=repo_owner,
            repo_name=repo_name,
            auth_token=auth_token,
        )

        call = analytics_task.run_no_wait(analytics_input)
        logger.info(f"Analytics task spawned: {call.workflow_run_id} for {codebase_name}")
        return call.workflow_run_id

    except Exception as e:
        logger.error(f"Failed to spawn analytics task for {codebase_name}: {e}")
        return None

