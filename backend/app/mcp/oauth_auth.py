"""
OAuth authentication configuration for MCP server using Auth0.
"""

import logging

from fastmcp.server.auth.providers.auth0 import Auth0Provider
from fastmcp.server.dependencies import get_access_token

from app.auth.models import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class OAuthAuthenticationError(Exception):
    """Exception raised when OAuth authentication or authorization fails"""


def create_mcp_oauth_provider() -> Auth0Provider:
    """
    Create Auth0Provider for MCP server OAuth authentication.

    Implementation based on: https://fastmcp.wiki/en/deployment/http#mounting-authenticated-servers

    URL Structure when mounted at /mcp:
    - Client connects to: {PUBLIC_BASE_URL}/mcp/v1
    - OAuth discovery (root level): {PUBLIC_BASE_URL}/.well-known/oauth-authorization-server
    - OAuth callbacks: {PUBLIC_BASE_URL}/mcp/auth/callback
    - MCP protocol: {PUBLIC_BASE_URL}/mcp/v1/*

    Discovery Flow (RFC 9470):
    1. Client tries /mcp/v1 -> gets 401 with resource_metadata URL
    2. Client fetches /.well-known/oauth-protected-resource/mcp/v1
    3. Client discovers OAuth server at /.well-known/oauth-authorization-server
    4. Client completes OAuth flow and retries /mcp/v1 with token
    """
    config_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration"
    mcp_full_url = f"{settings.PUBLIC_BASE_URL}/mcp"

    logger.info(f"Configuring MCP OAuth with Auth0 domain: {settings.AUTH0_DOMAIN}")
    logger.info(f"Public base URL: {settings.PUBLIC_BASE_URL}")
    logger.info(f"MCP mounted at: {mcp_full_url}")

    auth = Auth0Provider(
        config_url=config_url,
        client_id=settings.MCP_AUTH0_CLIENT_ID,
        client_secret=settings.MCP_AUTH0_CLIENT_SECRET,
        audience=settings.MCP_AUTH0_AUDIENCE,
        issuer_url=settings.PUBLIC_BASE_URL,
        base_url=mcp_full_url,
    )

    # TODO for prod!!! Must configure redis credential store here! Ideally don't merge into devlop till redis ready!

    return auth


def get_user_from_token() -> User:
    token = get_access_token()
    if not token or not hasattr(token, "claims"):
        raise OAuthAuthenticationError("No access token available")
    return User.model_validate(token.claims)


def get_organization_id_from_token() -> str:
    return get_user_from_token().organization_id


def get_user_id_from_token() -> str:
    return get_user_from_token().user_id
