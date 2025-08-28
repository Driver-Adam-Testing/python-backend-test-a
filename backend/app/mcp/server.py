import os
from inspect import cleandoc
from typing import Annotated, Any

from database.models_enums import PrimaryAssetKind
from pydantic import Field

# TODO move this or find somethign cleaner. not sure why we wouldn't want these hard coded.
FASTMCP_STATELESS_HTTP = True
FASTMCP_MASK_ERROR_DETAILS = True
os.environ["FASTMCP_STATELESS_HTTP"] = str(FASTMCP_STATELESS_HTTP)
os.environ["FASTMCP_MASK_ERROR_DETAILS"] = str(FASTMCP_MASK_ERROR_DETAILS)

import fastmcp
from database.db import get_session
from database.models import DerivedContent, Node, PrimaryAsset, Version
from database.models_enums import ContentKind, VersionStatus
from fastmcp import Context, FastMCP
from mcp_instructions import MCP_INSTRUCTIONS
from sqlmodel import select

from backend.app.mcp.mcp_instructions import MCP_INSTRUCTIONS

from .auth_middleware import McpAuthMiddleware, get_organization_id
from .code_map_v2 import get_code_map_simple
from .mcp_helpers import get_latest_version_for_codebase

CODEBASE_NAME_PARAM_DESCRIPTION = """Name of the Driver supported codebase.  The 'get_codebase_names' tool can be used to generate a list of supported codebases.  Only codebase names returned by this tool are valid for this parameter.
"""

my_mcp = FastMCP("Driver MCP Server", include_fastmcp_meta=False, instructions=MCP_INSTRUCTIONS)
assert (
    fastmcp.settings.stateless_http is True
), "FastMCP must be configured with stateless HTTP enabled."
assert (
    fastmcp.settings.mask_error_details is True
), "FastMCP must be configured to mask error details."

auth_middleware = McpAuthMiddleware()
my_mcp.add_middleware(auth_middleware)


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


@my_mcp.prompt(
    name="driver_init",
    description=cleandoc(
        """
        Initialization and instruction for how an LLM agent should optimally use Driver MCP tools. Call at the beginning of each session or anytime in a long agentic workflow wherein this context may have been lost.
        """
    ),
)
def driver_init() -> str:
    return MCP_INSTRUCTIONS


@my_mcp.tool(
    name="get_changelog",
    description=cleandoc(
        """
        Fetch the complete high-level changelog for a codebase, broken down by year and month.

        The codebase must be specified by name.

        Helpful for orienting and reasoning about a codebase -- use this in any context where the historical development process and decisions might be helpful. Prioritize calling this at the beginning of a task.
    """
    ),
)
def get_changelog(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
) -> str:
    """ """
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_CHANGELOG
    )
    return dc.content or str(dc.misc_metadata)


@my_mcp.tool(
    name="get_detailed_changelog",
    description=cleandoc(
        """
        Fetch the detailed changelog for a specific year and month of the given codebase.

        Use this when more detailed information about the development process of the codebase at a specific time might be helpful.
    """
    ),
)
def get_detailed_changelog(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
    year: Annotated[str, Field(description="The year of the changelog. (e.g. 2023)")],
    month: Annotated[
        str, Field(description="The month of the changelog. (e.g. 01, 02, ..., 12)")
    ],
) -> str:
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


@my_mcp.tool(
    name="get_codebase_names",
    description=cleandoc(
        """
        Get names of all codebases supported by the Driver MCP.
        Only returns codebases belonging to the authenticated user's Driver organization.

        All other Driver MCP tools will generally require a codebase name parameter. You must call this tool to get the list of valid codebase names. To resolve which codebase name is relevant for your tasks, you may want to use local tools such as `git` and facilities that print the name of the working directory. You can then cross-reference this with the list provided by this tool to ensure you pick the right one and properly call the other Driver MCP tools.
    """
    ),
    exclude_args=["dummy"],
)
def get_codebase_names(ctx: Context, dummy: str | None = None) -> list[str]:
    org_id = get_organization_id(ctx)
    return _get_codebase_names_for_org(org_id)


@my_mcp.tool(
    name="get_architecture_overview",
    description=cleandoc(
        """
    Get a complete architectural overview document for the specified codebase. You should prioritize fetching and reading this content at the beginning of any non-trivial task.
    """
    ),
)
def get_architecture_overview(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
) -> str:
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_ARCHITECTURE
    )
    return dc.content


@my_mcp.tool(
    name="get_llm_onboarding_guide",
    description=cleandoc(
        """
    Get an LLM onboarding guide document for the specified codebase. You should prioritize fetching and reading this content at the beginning of any non-trivial task.
    """
    ),
)
def get_llm_onboarding_guide(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
) -> str:
    org_id = get_organization_id(ctx)
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_LLM_ONBOARDING
    )
    return dc.content


@my_mcp.tool(
    name="get_file_documentation",
    description=cleandoc(
        """
        Get detailed symbol-level documentation for a specific file in a codebase.

        Use in tandem with `get_code_map` to effectively navigate a codebase and understand implementation details in files relevant for your tasks.
    """
    ),
)
def get_file_documentation(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
    path: Annotated[
        str,
        Field(
            description="The file path to get documentation. This should NOT include the codebase name (e.g., 'src/my_file.py' NOT 'codebase-name/src/utils/open.c').')."
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
    description=cleandoc(
        """
        Get a flat list of files and directories, with descriptions, under a given directory path.

        This tool explores directory structure - provide a directory path (not a file path).

        Use in tandem with `get_file_documentation` to effectively navigate a codebase and understand implementation details in files relevant for your tasks.

        Returns an object with:
        - payload: List of nodes, each containing:
          - path: The file/directory path
          - type: "file" or "directory"
          - description: A short sentence describing what the file/directory contains
        - errors: List of helpful error messages if no results found

        USAGE:
        - Use max_depth=0 to see only the directory itself
        - Use max_depth=1 to see the directory and its immediate children
        - Use max_depth=2 to include grandchildren
        - max_depth is relative to the specified path, not the codebase root
        - Provide directory paths only (e.g., "src", "src/utils", not "src/main.py")

        Examples:
        - List all top-level items: get_code_map("my-codebase", "", 1)
        - See what's in a directory: get_code_map("my-codebase", "services", 1)
        - Explore deeper: get_code_map("my-codebase", "api/handlers", 2)

        Further usage advice:
        - Prioritize using the `get_architecture_overview` and `get_llm_onboarding_guide` tools to get oriented with non-trivial tasks as a first step.
        - Then prioritize this tool when you want to subsequently explore parts of the codebase relevant to your task at hand.
        - Use this in tandem with `get_file_documentation`, where the latter can be used to return detailed symbol-level documentation for files of interest from using `get_code_map`.
    """
    ),
)
def get_code_map(
    ctx: Context,
    codebase_name: Annotated[
        str,
        Field(
            description="The name of the codebase, as it exists in Driver, to explore (e.g., 'my-codebase')"
        ),
    ],
    path: Annotated[
        str,
        Field(
            description="The directory path to explore (e.g., 'src', 'src/utils'). Use empty string for root. Should not include the codebase name (e.g., 'my-codebase/src' is incorrect)."
        ),
    ] = "",
    max_depth: Annotated[
        int,
        Field(
            description="Maximum depth to traverse relative to the specified path (0 = only the directory itself, 1 = directory + immediate children, etc.)",
            ge=0,
            le=20,
        ),
    ] = 2,
) -> dict[str, Any]:
    response = get_code_map_simple(
        org_id=get_organization_id(ctx),
        codebase_name=codebase_name,
        path=path,
        max_depth=max_depth,
    )
    return response.model_dump()
