import logging
from pathlib import Path

from database.db import get_session
from database.models_v1 import DerivedContent
from database.models_v2 import Node
from database.models_v2_enums import ContentKind, NodeKind
from pydantic import BaseModel
from sqlmodel import Session, select

from .mcp_helpers import get_latest_version_for_codebase

logger = logging.getLogger(__name__)


class CodeMapNode(BaseModel):
    path: str
    type: str
    description: str | None


class CodeMapResponse(BaseModel):
    payload: list[CodeMapNode]
    errors: list[str]


def get_code_map_simple(
    org_id: str,
    codebase_name: str,
    path: str = "",
    max_depth: int = 5,
) -> CodeMapResponse:
    path = str(Path(codebase_name) / path)
    logger.info(
        f"Getting code map for codebase '{codebase_name}', path '{path}', max_depth {max_depth}"
    )

    with get_session() as db:
        version = get_latest_version_for_codebase(db, org_id, codebase_name)
        if not version:
            logger.warning(
                f"No version found for codebase '{codebase_name}' in org '{org_id}'"
            )
            return CodeMapResponse(
                payload=[],
                errors=[
                    f"No completed version found for codebase '{codebase_name}'. "
                    f"Please ensure the codebase has been processed in Driver."
                ],
            )

        logger.info(f"Found version {version.id} for codebase '{codebase_name}'")

        nodes_with_content = _fetch_nodes_with_descriptions(
            db, version.id, path, max_depth
        )
        logger.info(f"Fetched {len(nodes_with_content)} nodes with content")

        nodes = _build_flat_node_list(nodes_with_content)
        logger.info(f"Built {len(nodes)} nodes for response")

        if not nodes:
            logger.warning(
                f"No nodes found for path '{path}' in codebase '{codebase_name}'"
            )
            return CodeMapResponse(
                payload=[],
                errors=[
                    f"No files or directories found under '{path}' for codebase '{codebase_name}'. "
                    f"Try a different directory path or increase max_depth (currently {max_depth})."
                ],
            )

        return CodeMapResponse(payload=nodes, errors=[])


def _fetch_nodes_with_descriptions(
    db: Session, version_id: str, path: str, max_depth: int
) -> list[tuple[Node, DerivedContent]]:
    path_filter = _normalize_path_filter(path)
    logger.info(
        f"Fetching nodes with path filter '{path_filter}' and max_depth {max_depth}"
    )

    result = db.exec(
        select(Node, DerivedContent)
        .join(DerivedContent, DerivedContent.node_id == Node.id)
        .where(Node.version_id == version_id)
        .where(Node.relative_path.like(path_filter))
        .where(Node.depth <= max_depth)
        .where(DerivedContent.content_kind == ContentKind.SHORT_SENTENCE_DESCRIPTION)
        .order_by(Node.relative_path)
    ).all()

    logger.info(f"Query returned {len(result)} nodes")
    return result


def _normalize_path_filter(path: str) -> str:
    if not path:
        return "%"

    # Ensure path ends with / for directory search
    normalized = path.rstrip("/") + "/%"
    logger.debug(f"Normalized path filter: '{path}' -> '{normalized}'")
    return normalized


def _build_flat_node_list(
    nodes_with_content: list[tuple[Node, DerivedContent]],
) -> list[CodeMapNode]:
    result = []

    for node, content in nodes_with_content:

        logger.debug(f"Adding node: path='{node.relative_path}', kind='{node.kind}'")

        result.append(
            CodeMapNode(
                path=node.relative_path,
                type="file" if node.kind == NodeKind.CODEBASE_FILE else "directory",
                description=content.content,
            )
        )

    logger.info(f"Built {len(result)} nodes from {len(nodes_with_content)} inputs")
    return result
