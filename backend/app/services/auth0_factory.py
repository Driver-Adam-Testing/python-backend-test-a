from shared.auth0.auth0_async import AsyncAuth0Service
from shared.auth0.auth0_service import Auth0Service

from app.core.config import settings


def create_auth0_service() -> Auth0Service:
    """Factory function to create Auth0Service with settings."""
    return Auth0Service(
        auth0_mgmt_domain=settings.AUTH0_MGMT_API_DOMAIN,
        auth0_mgmt_client_id=settings.AUTH0_MGMT_API_CLIENT_ID,
        auth0_mgmt_client_secret=settings.AUTH0_MGMT_API_CLIENT_SECRET,
        auth0_domain=settings.AUTH0_DOMAIN,
        auth0_client_id=settings.AUTH0_CLIENT_ID,
    )


def create_async_auth0_service() -> AsyncAuth0Service:
    """Factory function to create AsyncAuth0Service with settings."""
    return AsyncAuth0Service(
        auth0_mgmt_domain=settings.AUTH0_MGMT_API_DOMAIN,
        auth0_mgmt_client_id=settings.AUTH0_MGMT_API_CLIENT_ID,
        auth0_mgmt_client_secret=settings.AUTH0_MGMT_API_CLIENT_SECRET,
        auth0_domain=settings.AUTH0_DOMAIN,
        auth0_client_id=settings.AUTH0_CLIENT_ID,
    )
