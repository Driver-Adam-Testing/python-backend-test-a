import os

from database.models_v2_enums import PrimaryAssetKind

# TODO move this or find somethign cleaner. not sure why we wouldn't want these hard coded.
FASTMCP_STATELESS_HTTP = True
FASTMCP_MASK_ERROR_DETAILS = True
os.environ["FASTMCP_STATELESS_HTTP"] = str(FASTMCP_STATELESS_HTTP)
os.environ["FASTMCP_MASK_ERROR_DETAILS"] = str(FASTMCP_MASK_ERROR_DETAILS)

import fastmcp
from database.db import get_session
from database.models_v1 import DerivedContent
from database.models_v2 import Node, PrimaryAsset, Version
from database.models_v2_enums import ContentKind, VersionStatus
from fastmcp import Context, FastMCP
from sqlmodel import select

from .auth_middleware import McpAuthMiddleware, get_organization_id
from .auth_middleware import get_user as get_user_from_ctx

my_mcp = FastMCP("Driver MCP Server", include_fastmcp_meta=False)
assert (
    fastmcp.settings.stateless_http is True
), "FastMCP must be configured with stateless HTTP enabled."
assert (
    fastmcp.settings.mask_error_details is True
), "FastMCP must be configured to mask error details."

auth_middleware = McpAuthMiddleware()
my_mcp.add_middleware(auth_middleware)


@my_mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@my_mcp.tool(exclude_args=["dummy"])
def get_user(ctx: Context, dummy: str | None = None) -> dict:
    """Get the authenticated user (Who I am!)"""
    authd_user = get_user_from_ctx(ctx)
    return authd_user


def _get_root_node_content(
    org_id: str, codebase_name: str, content_kind: ContentKind
) -> DerivedContent | None:
    with get_session() as db:
        derived_content = db.exec(
            select(DerivedContent)
            .join(Node, Node.id == DerivedContent.node_id)
            .join(Version, Version.id == Node.version_id)
            .join(PrimaryAsset, PrimaryAsset.id == Version.primary_asset_id)
            .where(PrimaryAsset.display_name == codebase_name)
            .where(PrimaryAsset.organization_id == org_id)
            .where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
            .where(Version.status == VersionStatus.GENERATION_COMPLETE)
            .where(Node.depth == 0)
            .where(DerivedContent.content_kind == content_kind)
            .order_by(Version.updated_at.desc())
        ).first()  # Assumes one entry
        return derived_content


# @my_mcp.tool()
# def get_codebase_history_document(ctx: Context, codebase_name: str) -> str:
#     """
#     Get the history document for a codebase.
#     """
#     org_id = get_organization_id(ctx)
#     dc = _get_root_node_content(org_id, codebase_name, ContentKind.CODEBASE)
#     return dc.content or ""


@my_mcp.tool()
def get_codebase_audiences(ctx: Context, codebase_name: str) -> str:
    """
    Get the target audiences for a codebase.
    """
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(org_id, codebase_name, ContentKind.CODEBASE_AUDIENCES)
    return dc.content or str(dc.misc_metadata)


@my_mcp.tool()
def get_codebase_domains(ctx: Context, codebase_name: str) -> str:
    """
    Get the domains/areas that a codebase covers.
    """
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(org_id, codebase_name, ContentKind.CODEBASE_DOMAINS)
    return dc.content or str(dc.misc_metadata)


@my_mcp.tool()
def get_codebase_entry_points(ctx: Context, codebase_name: str) -> str:
    """
    Get the entry points for a codebase.
    """
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.CODEBASE_ENTRY_POINTS
    )
    return dc.content or str(dc.misc_metadata)


def _get_codebase_names_for_org(org_id: str) -> list[str]:
    """
    Get names of all codebases that have at least one completed version for a specific organization.
    """
    with get_session() as db:
        assets = db.exec(
            select(PrimaryAsset.display_name)
            .join(Version, Version.primary_asset_id == PrimaryAsset.id)
            .where(PrimaryAsset.organization_id == org_id)
            .where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
            .where(Version.status == VersionStatus.GENERATION_COMPLETE)
            .distinct()
        ).all()

        return assets


@my_mcp.tool(exclude_args=["dummy"])
def get_codebase_names(ctx: Context, dummy: str | None = None) -> list[str]:
    """
    Get names of all codebases we have Driver content for.
    Only returns codebases belonging to the authenticated user's Driver organization.

    You must call this tool to get the list of valid codebase names. You can provide this to further Driver MCP tool calls.
    To get your own codebase name, you may want to check git so you can pick a pertient result from the result of this tool.
    """
    org_id = get_organization_id(ctx)
    return _get_codebase_names_for_org(org_id)
