import os
from typing import Annotated, Any

from database.models_v2_enums import PrimaryAssetKind
from pydantic import Field

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
from .code_map_v2 import get_code_map_simple
from .mcp_helpers import get_latest_version_for_codebase

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


@my_mcp.tool()
def get_changelog(ctx: Context, codebase_name: str) -> str:
    """
    Fetch the complete high-level changelog for a codebase, broken down by year and month.
    """
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_CHANGELOG
    )
    return dc.content or str(dc.misc_metadata)


@my_mcp.tool()
def get_detailed_changelog(
    ctx: Context, codebase_name: str, year: str, month: str
) -> str:
    """
    Fetch the detailed changelog for a specific year and month of the given codebase.
    Args:
        codebase_name (str): The name of the codebase.
        year (str): The year of the changelog. (e.g. 2023)
        month (str): The month of the changelog. (e.g. 01, 02, ..., 12)
    """
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_CHANGELOG
    )
    return dc.misc_metadata.get(
        f"{year}-{month}", "No detailed changelog available for this month."
    )


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


@my_mcp.tool()
def get_architecture_overview(ctx: Context, codebase_name: str) -> str:
    """
    Get an architectural overview for the specified codebase
    Args:
        codebase_name (str): The name of the codebase.
    """
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_ARCHITECTURE
    )
    return dc.content


@my_mcp.tool()
def get_llm_onboarding_guide(ctx: Context, codebase_name: str) -> str:
    """
    Get an LLM onboarding guide for the specified codebase
    Args:
        codebase_name (str): The name of the codebase.
    """
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_LLM_ONBOARDING
    )
    return dc.content


@my_mcp.tool(
    description="Get detailed documentation for a specific file in a codebase."
)
def get_file_documentation(
    ctx: Context,
    codebase_name: Annotated[
        str, Field(description="The name of the codebase to explore")
    ],
    path: Annotated[
        str,
        Field(
            description="The file path to get documentation for (e.g., 'src/my_file.py', 'src/utils/open.c')."
        ),
    ],
) -> str:
    org_id = get_organization_id(ctx)

    with get_session() as db:
        version = get_latest_version_for_codebase(db, org_id, codebase_name)
        if not version:
            return f"Error: No completed documentation found for codebase '{codebase_name}'."

        full_path = f"{codebase_name}/{path.strip('/')}"

        node = db.exec(
            select(Node)
            .where(Node.version_id == version.id)
            .where(Node.relative_path == full_path)
        ).first()

        if not node:
            return f"Error: File '{path}' not found in codebase '{codebase_name}' documentation. "

        content = db.exec(
            select(DerivedContent)
            .where(DerivedContent.node_id == node.id)
            .where(DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION)
        ).first()

        if not content or not content.content:
            return f"No documentation available for '{path}' in codebase '{codebase_name}'. "
        return content.content


@my_mcp.tool(
    name="get_code_map",
    description="""Get a flat list of files and directories, with descriptions, under a given directory path.

    This tool explores directory structure - provide a directory path (not a file path).

    Returns an object with:
    - payload: List of nodes, each containing:
      - path: The file/directory path
      - type: "file" or "directory"
      - description: A short sentence describing what the file/directory contains
    - errors: List of helpful error messages if no results found

    OPTIMAL USAGE:
    - Use max_depth=5 for initial exploration
    - Increase max_depth for deeper analysis
    - Provide directory paths only (e.g., "src", "src/utils", not "src/main.py")

    Examples:
    - List all top-level items: get_code_map("my-codebase", "", 5)
    - Explore services: get_code_map("my-codebase", "services", 7)
    - Deep dive into API: get_code_map("my-codebase", "api/handlers", 10)""",
)
def get_code_map(
    ctx: Context,
    codebase_name: Annotated[
        str, Field(description="The name of the codebase to explore")
    ],
    path: Annotated[
        str,
        Field(
            description="The directory path to explore (e.g., 'src', 'src/utils'). Use empty string for root."
        ),
    ] = "",
    max_depth: Annotated[
        int,
        Field(
            description="Maximum depth to traverse in the directory tree", ge=0, le=20
        ),
    ] = 5,
) -> dict[str, Any]:
    response = get_code_map_simple(
        org_id=get_organization_id(ctx),
        codebase_name=codebase_name,
        path=path,
        max_depth=max_depth,
    )
    return response.model_dump()
