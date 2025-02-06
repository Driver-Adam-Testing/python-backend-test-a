from app.git_providers.core.config import GitProviderConfig
from database.models_v1 import GitProviderApp, GitProviderKind


def load_provider_config(app: GitProviderApp, client_secret: str) -> GitProviderConfig:
    if app.provider_kind in [
        GitProviderKind.GITLAB_ENTERPRISE_SELF_MANAGED,
    ]:
        return GitProviderConfig(
            application_id=app.id,
            name=app.name,
            provider_kind=app.provider_kind,
            base_url=app.base_url,
            client_id=app.client_id,
            client_secret=client_secret,
            redirect_uri=app.redirect_uri,
            scope=app.scopes,
            authorize_endpoint="oauth/authorize",
            token_endpoint="oauth/token",
            token_info_endpoint="oauth/token/info",
            user_endpoint="api/v4/user",
        )
    raise ValueError(f"Unsupported provider: {app.provider_kind}")
