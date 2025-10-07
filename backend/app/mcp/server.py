import os
from inspect import cleandoc
from typing import Annotated

from database.models_enums import PrimaryAssetKind
from pydantic import BaseModel, Field

# TODO move this or find somethign cleaner. not sure why we wouldn't want these hard coded.
FASTMCP_STATELESS_HTTP = True
FASTMCP_MASK_ERROR_DETAILS = True
os.environ["FASTMCP_STATELESS_HTTP"] = str(FASTMCP_STATELESS_HTTP)
os.environ["FASTMCP_MASK_ERROR_DETAILS"] = str(FASTMCP_MASK_ERROR_DETAILS)

import logging  # noqa: E402
from pathlib import Path  # noqa: E402

import fastmcp  # noqa: E402
from database.db import get_session  # noqa: E402
from database.models import DerivedContent, Node, PrimaryAsset, Version  # noqa: E402
from database.models_enums import ContentKind, VersionStatus  # noqa: E402
from fastmcp import Context, FastMCP  # noqa: E402
from fastmcp.exceptions import ToolError  # noqa: E402
from shared.prompts.structured_prompting import Component, Prompt  # noqa: E402
from sqlmodel import select  # noqa: E402

from .auth_middleware import McpAuthMiddleware, get_organization_id  # noqa: E402
from .code_map_v2 import CodeMap, get_code_map_simple  # noqa: E402
from .logging_middleware import McpLoggingMiddleware  # noqa: E402
from .mcp_helpers import get_latest_version_for_codebase  # noqa: E402

logger = logging.getLogger(__name__)

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
)
assert (
    fastmcp.settings.stateless_http is True
), "FastMCP must be configured with stateless HTTP enabled."
assert (
    fastmcp.settings.mask_error_details is True
), "FastMCP must be configured to mask error details."

auth_middleware = McpAuthMiddleware()
my_mcp.add_middleware(auth_middleware)

logging_middleware = McpLoggingMiddleware()
my_mcp.add_middleware(logging_middleware)


def _get_root_node_content(
    org_id: str, codebase_name: str, content_kind: ContentKind
) -> DerivedContent:
    with get_session() as db:
        primary_asset = db.exec(
            select(PrimaryAsset)
            .where(PrimaryAsset.display_name == codebase_name)
            .where(PrimaryAsset.organization_id == org_id)
            .where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
        ).first()

        if not primary_asset:
            raise ToolError(
                f"`{codebase_name}` is not codebase recognized by Driver.  Use the `get_codebase_names` tool to get a list of valid codebase names."
            )

        derived_content = db.exec(
            select(DerivedContent)
            .join(Node, Node.id == DerivedContent.node_id)
            .join(Version, Version.id == Node.version_id)
            .where(Version.primary_asset_id == primary_asset.id)
            .where(Version.status == VersionStatus.GENERATION_COMPLETE)
            .where(Node.depth == 0)
            .where(DerivedContent.content_kind == content_kind)
            .order_by(Version.updated_at.desc())
        ).first()

        if not derived_content:
            raise ToolError(
                f"No {content_kind.value} content exists for the `{codebase_name}` codebase."
            )

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


def _get_long_description(
    org_id: str,
    codebase_name: str,
    path: str,
) -> str:
    with get_session() as db:
        version = get_latest_version_for_codebase(db, org_id, codebase_name)
        if not version:
            raise ToolError(
                f"No completed documentation found for codebase '{codebase_name}'."
            )

        full_path = f"{codebase_name}/{path.strip('/')}"

        node = db.exec(
            select(Node)
            .where(Node.version_id == version.id)
            .where(Node.relative_path == full_path)
        ).first()

        if not node:
            raise ToolError(
                f"File '{path}' not found in codebase '{codebase_name}' documentation. "
            )

        content = db.exec(
            select(DerivedContent)
            .where(DerivedContent.node_id == node.id)
            .where(DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION)
        ).first()

        if not content or not content.content:
            raise ToolError(
                f"No documentation available for '{path}' in codebase '{codebase_name}'. "
            )
        return content.content


class FileDocumentationResponse(BaseModel):
    content: str
    lines_returned: int
    next_line: int | None
    lines_remaining: int
    next_section: str | None


def _apply_file_doc_pagination(
    markdown_text: str, start_line: int, max_lines: int
) -> FileDocumentationResponse:
    if not markdown_text:
        raise ToolError("No documentation available for the file.")

    if start_line < 1:
        raise ToolError("Start line must be greater than or equal to 1.")

    if max_lines < 0:
        raise ToolError("Max lines must be greater than or equal to 0.")

    full_text = markdown_text.split("\n")

    if start_line > len(full_text):
        raise ToolError(
            f"Start line {start_line} is greater than the number of lines in the file ({len(full_text)})"
        )

    start_idx = start_line - 1

    # return what's left of the file
    if (start_idx + max_lines >= len(full_text)) or max_lines == 0:
        content_lines = full_text[start_idx:]

        return FileDocumentationResponse(
            content="\n".join(content_lines),
            lines_returned=len(content_lines),
            next_line=None,
            lines_remaining=0,
            next_section=None,
        )

    end_idx = start_idx + max_lines - 1
    partial_text = full_text[start_idx : end_idx + 1]

    # we just happened to stop at the end of a section
    if full_text[end_idx + 1].lstrip().startswith("#"):
        return FileDocumentationResponse(
            content="\n".join(partial_text),
            lines_returned=len(partial_text),
            next_line=end_idx + 2,
            lines_remaining=len(full_text) - end_idx - 1,
            next_section=full_text[end_idx + 1].lstrip().lstrip("#").strip(),
        )

    # we landed in the middle or start of a section
    for idx in reversed(range(len(partial_text))):
        if partial_text[idx].lstrip().startswith("#") and idx != 0:
            return FileDocumentationResponse(
                content="\n".join(partial_text[:idx]),
                lines_returned=len(partial_text[:idx]),
                next_line=idx + start_idx + 1,
                lines_remaining=len(full_text) - idx - start_idx,
                next_section=partial_text[idx].lstrip().lstrip("#").strip(),
            )

    # we started in the middle of a section that was too long
    return FileDocumentationResponse(
        content="\n".join(partial_text),
        lines_returned=len(partial_text),
        next_line=end_idx + 2,
        lines_remaining=len(full_text) - end_idx - 1,
        next_section=None,
    )


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
def get_file_documentation(
    ctx: Context,
    codebase_name: Annotated[str, Field(description=CODEBASE_NAME_PARAM_DESCRIPTION)],
    path: Annotated[
        str,
        Field(
            description="The file path to get documentation. This should NOT include the codebase name (e.g., 'src/my_file.py' NOT 'codebase-name/src/utils/open.c').')."
        ),
    ],
    start_line: Annotated[
        int,
        Field(
            description="The line number to start from.  ALWAYS use 1 for the first call.",
            ge=1,
        ),
    ],
    max_lines: Annotated[
        int,
        Field(
            description="The maximum number of lines to return. 0 means no limit.  ALWAYS use 0 for the first call.",
            ge=0,
        ),
    ],
) -> FileDocumentationResponse:
    org_id = get_organization_id(ctx=ctx)
    markdown_text = _get_long_description(
        org_id=org_id, codebase_name=codebase_name, path=path
    )
    return _apply_file_doc_pagination(
        markdown_text=markdown_text, start_line=start_line, max_lines=max_lines
    )


class CodeMapResponse(BaseModel):
    code_map: CodeMap
    nodes_returned: int
    next_node: int | None
    nodes_remaining: int


def _apply_code_map_pagination(
    code_map: CodeMap, start_node: int, max_nodes: int
) -> CodeMapResponse:
    total_nodes = len(code_map.payload)

    if start_node < 0:
        raise ToolError("Start node must be greater than or equal to 0.")

    if max_nodes < 0:
        raise ToolError("Max nodes must be greater than or equal to 0.")

    if start_node >= total_nodes:
        raise ToolError(
            f"Start node {start_node} is greater than or equal to the total number of nodes ({total_nodes})"
        )

    if max_nodes == 0 or start_node + max_nodes >= total_nodes:
        paginated_nodes = code_map.payload[start_node:]

        return CodeMapResponse(
            code_map=CodeMap(payload=paginated_nodes),
            nodes_returned=len(paginated_nodes),
            next_node=None,
            nodes_remaining=0,
        )

    paginated_nodes = code_map.payload[start_node : start_node + max_nodes]
    next_node = start_node + max_nodes
    nodes_remaining = total_nodes - next_node

    return CodeMapResponse(
        code_map=CodeMap(payload=paginated_nodes),
        nodes_returned=len(paginated_nodes),
        next_node=next_node,
        nodes_remaining=nodes_remaining,
    )


@my_mcp.tool(
    name="get_code_map",
    description=cleandoc(
        """
        Get a flat list of files and directories, with descriptions, under a given directory path.

        This tool explores directory structure - provide a directory path (not a file path).

        Use in tandem with `get_file_documentation` to effectively navigate a codebase and understand implementation details in files relevant for your tasks.

        Returns an object with:
        - code_map: Object containing:
          - payload: List of nodes, each containing:
            - path: The file/directory path
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
) -> CodeMapResponse:
    code_map = get_code_map_simple(
        org_id=get_organization_id(ctx),
        codebase_name=codebase_name,
        path=path,
        max_depth=max_depth,
    )

    return _apply_code_map_pagination(
        code_map=code_map,
        start_node=start_node,
        max_nodes=max_nodes,
    )
