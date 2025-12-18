import os
from inspect import cleandoc
from typing import Annotated
import truststore

from pydantic import Field

# TODO move this or find somethign cleaner. not sure why we wouldn't want these hard coded.
FASTMCP_STATELESS_HTTP = True
FASTMCP_MASK_ERROR_DETAILS = True
os.environ["FASTMCP_STATELESS_HTTP"] = str(FASTMCP_STATELESS_HTTP)
os.environ["FASTMCP_MASK_ERROR_DETAILS"] = str(FASTMCP_MASK_ERROR_DETAILS)

import logging  # noqa: E402
from pathlib import Path  # noqa: E402

import fastmcp  # noqa: E402
from fastmcp import Context, FastMCP  # noqa: E402
from shared.prompts.structured_prompting import Component, Prompt  # noqa: E402
from shared.tool_executors import (  # noqa: E402
    ToolUseError,
    get_architecture_overview,
    get_changelog,
    get_code_map,
    get_codebase_names,
    get_detailed_changelog,
    get_file_documentation,
    get_llm_onboarding_guide,
)

from .icons import driver_logo_svg  # noqa: E402
from .logging_middleware import (  # noqa: E402
    DriverMcpToolResponse,
    McpLoggingMiddleware,
)
from .oauth_auth import (  # noqa: E402
    create_mcp_oauth_provider,
    get_organization_id_from_token,
    get_user_id_from_token,
)

logger = logging.getLogger(__name__)
truststore.inject_into_ssl()

CODEBASE_NAME_PARAM_DESCRIPTION = """Name of the Driver supported codebase.  The 'get_codebase_names' tool can be used to generate a list of supported codebases.  Only codebase names returned by this tool are valid for this parameter.
"""


def _get_instructions_from_file(instructions_file: Path) -> str:
    try:
        with open(instructions_file) as f:
            raw_instructions = f.read()
    except FileNotFoundError:
        raise ValueError(f"Instructions file not found: {instructions_file}")

    return Prompt.empty().append(Component(string=raw_instructions)).into_str()


INSTRUCTIONS_FILE = Path(__file__).parent / "_AGENTS.md"

MCP_INSTRUCTIONS = _get_instructions_from_file(INSTRUCTIONS_FILE)

my_mcp = FastMCP(
    "Driver MCP Server",
    include_fastmcp_meta=False,
    instructions=MCP_INSTRUCTIONS,
    icons=[
        driver_logo_svg,
    ],
)
assert (
    fastmcp.settings.stateless_http is True
), "FastMCP must be configured with stateless HTTP enabled."
assert (
    fastmcp.settings.mask_error_details is True
), "FastMCP must be configured to mask error details."

auth_provider = create_mcp_oauth_provider()
my_mcp.auth = auth_provider

logging_middleware = McpLoggingMiddleware()
my_mcp.add_middleware(logging_middleware)


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
def get_codebase_names_tool(
    ctx: Context, dummy: str | None = None
) -> DriverMcpToolResponse:
    try:
        org_id = get_organization_id_from_token()
        user_id = get_user_id_from_token()
        payload = get_codebase_names(org_id=org_id, user_id=user_id)
        return DriverMcpToolResponse(payload=payload, error_message=None)
    except ToolUseError as e:
        return DriverMcpToolResponse(payload=None, error_message=e.agent_message)


@my_mcp.tool(
    name="get_architecture_overview",
    description=cleandoc(
        """
    Get a complete architectural overview document for the specified codebase. You should prioritize fetching and reading this content at the beginning of any non-trivial task.
    """
    ),
)
def get_architecture_overview_tool(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
) -> DriverMcpToolResponse:
    try:
        org_id = get_organization_id_from_token()
        user_id = get_user_id_from_token()
        payload = get_architecture_overview(
            org_id=org_id, codebase_name=codebase_name, user_id=user_id
        )
        return DriverMcpToolResponse(payload=payload, error_message=None)
    except ToolUseError as e:
        return DriverMcpToolResponse(payload=None, error_message=e.agent_message)


@my_mcp.tool(
    name="get_llm_onboarding_guide",
    description=cleandoc(
        """
    Get an LLM onboarding guide document for the specified codebase. You should prioritize fetching and reading this content at the beginning of any non-trivial task.
    """
    ),
)
def get_llm_onboarding_guide_tool(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
) -> DriverMcpToolResponse:
    try:
        org_id = get_organization_id_from_token()
        user_id = get_user_id_from_token()
        payload = get_llm_onboarding_guide(
            org_id=org_id, codebase_name=codebase_name, user_id=user_id
        )
        return DriverMcpToolResponse(payload=payload, error_message=None)
    except ToolUseError as e:
        return DriverMcpToolResponse(payload=None, error_message=e.agent_message)


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
def get_changelog_tool(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
) -> DriverMcpToolResponse:
    try:
        org_id = get_organization_id_from_token()
        user_id = get_user_id_from_token()
        payload = get_changelog(
            org_id=org_id, codebase_name=codebase_name, user_id=user_id
        )
        return DriverMcpToolResponse(payload=payload, error_message=None)
    except ToolUseError as e:
        return DriverMcpToolResponse(payload=None, error_message=e.agent_message)


@my_mcp.tool(
    name="get_detailed_changelog",
    description=cleandoc(
        """
        Fetch the detailed changelog for a specific year and month of the given codebase.

        Use this when more detailed information about the development process of the codebase at a specific time might be helpful.
    """
    ),
)
def get_detailed_changelog_tool(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
    year: Annotated[str, Field(description="The year of the changelog. (e.g. 2023)")],
    month: Annotated[
        str, Field(description="The month of the changelog. (e.g. 01, 02, ..., 12)")
    ],
) -> DriverMcpToolResponse:
    try:
        org_id = get_organization_id_from_token()
        user_id = get_user_id_from_token()
        payload = get_detailed_changelog(
            org_id=org_id,
            codebase_name=codebase_name,
            year=year,
            month=month,
            user_id=user_id,
        )
        return DriverMcpToolResponse(payload=payload, error_message=None)
    except ToolUseError as e:
        return DriverMcpToolResponse(payload=None, error_message=e.agent_message)


@my_mcp.tool(
    name="get_file_documentation",
    description=cleandoc(
        """
    Get detailed symbol-level documentation for a specific file in a codebase.

    Usage Patterns:
    1. Full file: Set start_line=1, max_lines=0 (reads entire file).  ALWAYS use this pattern for the first call.
    2. Large files (when you hit token limits):
        - First call: start_line=1, max_lines=500
        - Next calls: Use next_line from previous response, max_lines=500
        - Continue until lines_remaining=0

    Response includes pagination fields:
    - lines_returned: Number of lines in this response
    - next_line: Line number for your next call (null when done)
    - lines_remaining: How many lines are left to read
    - next_section: Preview of what content comes next (null at EOF)

    Example pagination workflow:
    1. Call with start_line=1, max_lines=500
    2. Check response.lines_remaining > 0
    3. Call with start_line=response.next_line, max_lines=500
    4. Repeat until lines_remaining=0

    Use in tandem with `get_code_map` to effectively navigate a codebase and understand implementation details in files relevant for your tasks.
    """
    ),
)
def get_file_documentation_tool(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
    relative_file_path: Annotated[
        str,
        Field(
            description="The file path to get documentation for, relative to the codebase root. This should NOT include the root directory name (e.g., 'src/my_file.py' NOT 'my-codebase/src/utils/open.c').')."
        ),
    ],
    start_line: Annotated[
        int,
        Field(
            description="The line number to start from.  ALWAYS use 1 for the first call.",
            ge=1,
        ),
    ] = 1,
    max_lines: Annotated[
        int,
        Field(
            description="The maximum number of lines to return. 0 means no limit.  ALWAYS use 0 for the first call.",
            ge=0,
        ),
    ] = 0,
) -> DriverMcpToolResponse:
    try:
        org_id = get_organization_id_from_token()
        user_id = get_user_id_from_token()
        payload = get_file_documentation(
            org_id=org_id,
            codebase_name=codebase_name,
            path=relative_file_path,
            start_line=start_line,
            max_lines=max_lines,
            user_id=user_id,
        )
        return DriverMcpToolResponse(payload=payload, error_message=None)
    except ToolUseError as e:
        return DriverMcpToolResponse(payload=None, error_message=e.agent_message)


@my_mcp.tool(
    name="get_code_map",
    description=cleandoc(
        """
        Get a flat list of files and directories, with descriptions, under a given directory path.

        This tool explores directory structure - provide a directory path (not a file path).

        Use in tandem with `get_file_documentation` to effectively navigate a codebase and understand implementation details in files relevant for your tasks.

        Returns an object with:
        - code_map: List of nodes, each containing:
            - absolute_path: The file/directory path including the codebase root
            - type: "file" or "directory"
            - description: A short sentence describing what the file/directory contains
        - nodes_returned: Number of nodes in this response
        - next_node: Node index for your next call (null when done)
        - nodes_remaining: How many nodes are left to read

        Usage Patterns:
        1. Full result: Set start_node=0, max_nodes=0 (reads all nodes). ALWAYS use this pattern for the first call.
        2. Large results (when you hit token limits):
            - First call: start_node=0, max_nodes=50
            - Next calls: Use next_node from previous response, max_nodes=50
            - Continue until nodes_remaining=0

        Example pagination workflow:
        1. Call with start_node=0, max_nodes=50
        2. Check response.nodes_remaining > 0
        3. Call with start_node=response.next_node, max_nodes=50
        4. Repeat until nodes_remaining=0

        USAGE:
        - Use max_depth=0 to see only the directory itself
        - Use max_depth=1 to see the directory and its immediate children
        - Use max_depth=2 to include grandchildren
        - max_depth is relative to the specified path, not the codebase root
        - Provide relative directory paths only (e.g., "src", "src/utils", not "src/main.py")

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
def get_code_map_tool(
    ctx: Context,
    codebase_name: Annotated[
        str,
        Field(
            description="The name of the codebase, as it exists in Driver, to explore (e.g., 'my-codebase')"
        ),
    ],
    relative_directory_path: Annotated[
        str,
        Field(
            description="The directory path to explore, relative to the codebase root (e.g., 'src', 'src/utils'). Use empty string for root. Should not include the root directory name (e.g., 'my-codebase/src' is incorrect)."
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
    start_node: Annotated[
        int,
        Field(
            description="The node index to start from. ALWAYS use 0 for the first call.",
            ge=0,
        ),
    ] = 0,
    max_nodes: Annotated[
        int,
        Field(
            description="The maximum number of nodes to return. 0 means no limit. ALWAYS use 0 for the first call.",
            ge=0,
        ),
    ] = 0,
) -> DriverMcpToolResponse:
    try:
        org_id = get_organization_id_from_token()
        user_id = get_user_id_from_token()
        payload = get_code_map(
            org_id=org_id,
            codebase_name=codebase_name,
            path=relative_directory_path,
            max_depth=max_depth,
            start_node=start_node,
            max_nodes=max_nodes,
            user_id=user_id,
        )
        return DriverMcpToolResponse(payload=payload, error_message=None)
    except ToolUseError as e:
        return DriverMcpToolResponse(payload=None, error_message=e.agent_message)
