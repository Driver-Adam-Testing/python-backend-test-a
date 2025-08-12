import logging

# TODO DO NOT LEAK STACK TRACES TO CLIENTS!!!!!!!!!!!!!!!!!!!!!!!!!!! Figure out
from fastmcp import Context
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

from app.auth.api_key_async import verify_api_key_async
from app.services.auth0_async import AsyncAuth0Service

logger = logging.getLogger(__name__)


class McpAuthMiddleware(Middleware):
    def __init__(self) -> None:
        super().__init__()
        self.auth0 = AsyncAuth0Service()

    async def on_message(self, context: MiddlewareContext, call_next: any) -> any:
        try:
            # NOTE: Only works with http transport!
            api_key = self._extract_api_key(get_http_headers())

            if not api_key:
                raise AuthenticationError("Missing API key")

            user_data = await verify_api_key_async(api_key, self.auth0)

            # Store auth data in FastMCP context
            # This makes it available to all downstream tools
            context.fastmcp_context.set_state("organization_id", user_data["org_id"])
            context.fastmcp_context.set_state("user_id", user_data["sub"])
            context.fastmcp_context.set_state("user", user_data)
            # context.fastmcp_context.set_state("authenticated", True)

            logger.info(
                f"Authenticated user {user_data['sub']} for org {user_data['org_id']} in FastMCP context"
            )

        except Exception as e:
            # Log full traceback for debugging
            logger.exception("Authentication failed with exception:")

            # Convert FastAPI HTTPException to MCP-appropriate error
            if hasattr(e, "status_code") and e.status_code == 401:
                # Expected auth failures - just log the message
                logger.info(f"Authentication rejected: {e.detail}")
                raise AuthenticationError(str(e.detail))

            # For unexpected errors, don't leak internal details to client
            raise AuthenticationError("Authentication failed due to internal error")

        return await call_next(context)

    def _extract_api_key(self, headers: dict[str, str]) -> str | None:
        # Check X-API-Key header (case-insensitive)
        for key, value in headers.items():
            if key.lower() == "x-api-key":
                return value
        return None


class AuthenticationError(Exception):
    """Custom exception for authentication failures"""


# TODO move these elsewhere, not part of middleware directly.
def get_organization_id(ctx: Context) -> str:
    org_id = ctx.get_state("organization_id")
    if not org_id:
        raise AuthenticationError("No organization context available")
    return org_id


def get_user_id(ctx: Context) -> str:
    """Get the authenticated user ID from context"""
    user_id = ctx.get_state("user_id")
    if not user_id:
        raise AuthenticationError("No user context available")
    return user_id


def get_user(ctx: Context) -> dict:
    """Get the full user object from context"""
    user = ctx.get_state("user")
    if not user:
        raise AuthenticationError("No user context available")
    return user
