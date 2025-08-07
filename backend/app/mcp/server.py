from database.db import get_session
from database.models_v2 import PrimaryAsset
from fastmcp import Context, FastMCP
from sqlmodel import select

from .auth_middleware import McpAuthMiddleware, get_organization_id
from .auth_middleware import get_user as get_user_from_ctx

my_mcp = FastMCP(
    "Driver MCP Server",
    instructions="This is a demo Driver MCP Server",
    stateless_http=True,
)
auth_middleware = McpAuthMiddleware()
my_mcp.add_middleware(auth_middleware)


@my_mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@my_mcp.tool()
def get_user(name: str, ctx: Context) -> dict:
    """Get the authenticated user (Who I am!)"""
    authd_user = get_user_from_ctx(ctx)
    return authd_user


def get_primary_assets(ctx: Context) -> list[PrimaryAsset]:
    """
    Get all primary asset
    """
    org_id = get_organization_id(ctx)
    with get_session() as db:
        assets = db.exec(
            select(PrimaryAsset).where(PrimaryAsset.organization_id == org_id)
        ).all()
    return assets


@my_mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
