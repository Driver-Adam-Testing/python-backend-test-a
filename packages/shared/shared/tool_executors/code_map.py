import logging
from pathlib import Path

from database.db import get_session
from database.models import DerivedContent, Node, VersionNode
from database.models_enums import ContentKind, NodeKind
from pydantic import BaseModel
from sqlmodel import Session, select

from .tool_use_error import ToolUseError
from .utilities import get_latest_version_for_codebase

logger = logging.getLogger(__name__)


class CodeMapNode(BaseModel):
    absolute_path: str
    type: str
    description: str | None


class _CodeMap(BaseModel):
    payload: list[CodeMapNode]


class CodeMapResponse(BaseModel):
    code_map: list[CodeMapNode]
    nodes_returned: int
    next_node: int | None
    nodes_remaining: int


def _fetch_code_map_data(
    db: Session, version_id: str, path: str, max_depth: int
) -> list[tuple[VersionNode, DerivedContent, Node]]:
    path_filter = _normalize_path_filter(path)

    # Calculate base depth: number of path components in the search path
    # e.g., "codebase-name/src" has base_depth of 1 (counting after codebase-name/)
    base_depth = len(Path(path).parts) - 1 if path else 0

    logger.info(
        f"Fetching nodes with path filter '{path_filter}', base_depth {base_depth}, max_depth {max_depth}"
    )

    result = db.exec(
        select(VersionNode, DerivedContent, Node)
        .join(Node, Node.id == VersionNode.node_id)
        .join(DerivedContent, DerivedContent.node_id == Node.id)
        .where(VersionNode.version_id == version_id)
        .where(VersionNode.relative_path.like(path_filter))
        .where(VersionNode.depth <= base_depth + max_depth)
        .where(DerivedContent.content_kind == ContentKind.SHORT_SENTENCE_DESCRIPTION)
        .order_by(VersionNode.relative_path)
    ).all()

    logger.info(f"Query returned data for {len(result)} nodes")
    return result


def _normalize_path_filter(path: str) -> str:
    if not path:
        return "%"

    normalized = path.rstrip("/") + "/%"
    logger.debug(f"Normalized path filter: '{path}' -> '{normalized}'")
    return normalized


def _build_flat_code_map_node_list(
    code_map_data: list[tuple[VersionNode, DerivedContent, Node]],
) -> list[CodeMapNode]:
    result = []

    for version_node, content, node in code_map_data:
        logger.debug(
            f"Adding code map node: path='{version_node.relative_path}', kind='{node.kind}'"
        )

        result.append(
            CodeMapNode(
                absolute_path=version_node.relative_path,
                type="file" if node.kind == NodeKind.CODEBASE_FILE else "directory",
                description=content.content,
            )
        )

    logger.info(f"Built {len(result)} nodes from {len(code_map_data)} inputs")
    return result


def get_code_map_simple(
    org_id: str,
    codebase_name: str,
    user_id: str,
    path: str = "",
    max_depth: int = 5,
) -> _CodeMap:
    path = str(Path(codebase_name) / path)
    logger.info(
        f"Getting code map for codebase '{codebase_name}', path '{path}', max_depth {max_depth}"
    )

    with get_session() as db:
        version = get_latest_version_for_codebase(db, org_id, codebase_name, user_id)
        if not version:
            raise ToolUseError(
                agent_message=f"No completed version found for codebase '{codebase_name}', or user is unauthorized. "
            )

        logger.info(f"Found version {version.id} for codebase '{codebase_name}'")

        nodes_with_content = _fetch_code_map_data(db, version.id, path, max_depth)
        logger.info(f"Fetched {len(nodes_with_content)} nodes with content")

        nodes = _build_flat_code_map_node_list(nodes_with_content)
        logger.info(f"Built {len(nodes)} nodes for response")

        if not nodes:
            raise ToolUseError(
                agent_message=f"No files or directories found under '{path}' for codebase '{codebase_name}'. "
                f"Try a different directory path or increase max_depth (currently {max_depth})."
            )

        return _CodeMap(payload=nodes)


def _apply_code_map_pagination(
    code_map: _CodeMap, start_node: int, max_nodes: int
) -> CodeMapResponse:
    total_nodes = len(code_map.payload)

    if start_node < 0:
        raise ToolUseError(
            agent_message="Start node must be greater than or equal to 0."
        )

    if max_nodes < 0:
        raise ToolUseError(
            agent_message="Max nodes must be greater than or equal to 0."
        )

    if start_node >= total_nodes:
        raise ToolUseError(
            agent_message=f"Start node {start_node} is greater than or equal to the total number of nodes ({total_nodes})"
        )

    if max_nodes == 0 or start_node + max_nodes >= total_nodes:
        paginated_nodes = code_map.payload[start_node:]

        return CodeMapResponse(
            code_map=paginated_nodes,
            nodes_returned=len(paginated_nodes),
            next_node=None,
            nodes_remaining=0,
        )

    paginated_nodes = code_map.payload[start_node : start_node + max_nodes]
    next_node = start_node + max_nodes
    nodes_remaining = total_nodes - next_node

    return CodeMapResponse(
        code_map=paginated_nodes,
        nodes_returned=len(paginated_nodes),
        next_node=next_node,
        nodes_remaining=nodes_remaining,
    )


def get_code_map(
    org_id: str,
    codebase_name: str,
    path: str,
    max_depth: int,
    start_node: int,
    max_nodes: int,
    user_id: str,
) -> CodeMapResponse:
    code_map = get_code_map_simple(
        org_id=org_id,
        codebase_name=codebase_name,
        user_id=user_id,
        path=path,
        max_depth=max_depth,
    )

    return _apply_code_map_pagination(
        code_map=code_map,
        start_node=start_node,
        max_nodes=max_nodes,
    )
