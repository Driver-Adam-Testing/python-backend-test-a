from typing import Any

from database.db import get_session
from database.models_v1 import DerivedContent
from database.models_v2 import Node, PrimaryAsset, Version
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.routes.v2.query_utils import (
    PaginationQueryParams,
    SortDirection,
    apply_filters_to_query,
    apply_sorting_to_query,
)
from app.api.routes.v2.schemas import ListWithCount
from app.core.logger import logger

# from ..schemas.content_schema import ListContentInput
# from ..services import content_service


def _fetch_content_nodes(
    org_id: str,
    version_id: str,
    path: str,
    max_depth: int,
    include_driver_docs: bool = False,
) -> dict[str, Any]:
    """
    Get a hierarchical view of the codebase structure optimized for LLM exploration.
    Arguments:
        path (str): The path to the codebase or subdirectory to explore.
        max_depth (int): The maximum depth to explore in the codebase structure.
        include_driver_docs (bool): Whether to include files with Driver documentation.
    """
    query = (
        select(DerivedContent)
        .options(
            selectinload(DerivedContent.node)
            .selectinload(Node.version)
            .selectinload(Version.primary_asset)
            .selectinload(PrimaryAsset.tags)
        )
        .where(
            DerivedContent.node.has(
                Node.version.has(
                    Version.primary_asset.has(
                        PrimaryAsset.organization_id == org_id,
                    )
                )
            )
        )
    )
    node_kinds = ["CODEBASE_DIRECTORY", "CODEBASE_FILE"]
    path_filter = (f"{path}%",)
    # version_id = "2fd2b190-d31e-4383-8b7c-8ea7b35ac1de",
    content_kind = ("long_description",)
    sort_by = ("node.relative_path",)
    sort_direction = "ASC"
    # Build query parameters
    params = {
        "node.kind__in": ",".join(node_kinds),
        "content_kind__eq": content_kind,
        "node.relative_path__ilike": path_filter,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
        "node.version_id": version_id,
        "node.depth__lte": max_depth,
        "limit": 1000,  # Adjust as needed
    }
    with get_session() as session:
        filters = dict(params)
        query = apply_filters_to_query(query, filters, DerivedContent)
        count_query = select(func.count()).select_from(query.subquery())
        total_count = session.exec(count_query).one()
        pagination = PaginationQueryParams(
            limit=1000,
            offset=0,
            # sort_by=sort_by,
            sort_direction=SortDirection.ASC,
        )
        query = apply_sorting_to_query(query, pagination, DerivedContent)
        result = session.exec(query)
        contents = result.all()
        # Transform results to a list of dictionaries
        results = []
        for content in contents:
            content_model = content.model_dump()
            node = content.node.model_dump()
            results.append(
                {
                    **content_model,
                    "node": node,
                }
            )
        return ListWithCount(results=results, total_count=total_count).model_dump()
        # do the transformation to the hierarchical structure


def _build_tree_structure(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    tree = {}

    # Sort nodes by path for consistent processing
    nodes.sort(key=lambda x: x.get("relative_path", ""))

    for node_data in nodes:
        node = node_data.get("node", {})
        description = node_data.get("content", {})

        relative_path = node_data.get("relative_path", "")
        node_kind = node.get("kind", "")

        # Skip nodes without valid paths
        if not relative_path:
            continue

        # Remove prefix if present (e.g., "python-backend/")
        # if relative_path.startswith(self.config.driver_docs_prefix):
        #     relative_path = relative_path[len(self.config.driver_docs_prefix):]

        # Skip empty paths after prefix removal
        if not relative_path:
            # Handle root directory case
            if node_kind == "CODEBASE_DIRECTORY":
                if "" not in tree:
                    tree[""] = {
                        "_type": "directory",
                        "_has_driver_doc": True,
                        "_description": description,
                    }
            continue

        # Split path into components
        path_parts = relative_path.split("/")
        # Remove empty parts (from trailing slashes)
        path_parts = [part for part in path_parts if part]

        if not path_parts:
            continue

        # Navigate/create tree structure
        current = tree
        for i, part in enumerate(path_parts):
            is_last_part = i == len(path_parts) - 1

            if part not in current:
                # Determine if this is a file or directory
                if is_last_part:
                    node_type = "file" if node_kind == "CODEBASE_FILE" else "directory"
                else:
                    node_type = "directory"

                # Check if driver docs exist for this path
                # For now, assume no driver docs unless we can verify
                has_driver_doc = True

                current[part] = {
                    "_type": node_type,
                    "_has_driver_doc": has_driver_doc,
                    "_description": None,
                }

            # Update the final node with actual data from API
            if is_last_part:
                current[part]["_description"] = description
                current[part]["_type"] = (
                    "file" if node_kind == "CODEBASE_FILE" else "directory"
                )

            # Move to next level for directories
            if not is_last_part:
                current = current[part]

    return tree


def _validate_tree_schema(tree: dict[str, Any]) -> bool:
    """
    Validate tree structure against codemap JSON schema.

    Args:
        tree: Tree structure to validate

    Returns:
        True if valid, False otherwise
    """

    def validate_node(node: Any) -> bool:
        if not isinstance(node, dict):
            return False

        # Check required fields
        required_fields = ["_type", "_has_driver_doc", "_description"]
        for field in required_fields:
            if field not in node:
                return False

        # Validate field types
        if node["_type"] not in ["file", "directory"]:
            return False

        if not isinstance(node["_has_driver_doc"], bool):
            return False

        if node["_description"] is not None and not isinstance(
            node["_description"], str
        ):
            return False

        # Recursively validate child nodes
        for key, value in node.items():
            if not key.startswith("_"):
                if not validate_node(value):
                    return False

        return True

    # Validate root level
    if not isinstance(tree, dict):
        return False

    # Validate each root node
    for key, node in tree.items():
        if key.startswith("_"):
            return False  # Root level shouldn't have metadata fields
        if not validate_node(node):
            return False

    return True


def get_code_map(
    org_id: str,
    path_filter: str,
    version_id: str,
    max_depth: int = 5,
    validate_schema: bool = True,
) -> dict[str, Any] | dict[str, str]:
    """
    Fetch content nodes and transform to codemap format.

    Args:
        org_id: Organization ID to filter nodes
        path_filter: Path filter pattern for nodes
        version_id: Version ID for the nodes
        max_depth: Maximum depth to traverse
        validate_schema: Whether to validate against codemap schema

    Returns:
        Codemap tree structure or error response
    """
    try:
        # Fetch raw content nodes
        raw_data = _fetch_content_nodes(
            org_id=org_id,
            version_id=version_id,
            path=path_filter,
            max_depth=max_depth,
            include_driver_docs=True,
        )

        # Extract nodes from response
        nodes = raw_data.get("results", [])
        if not nodes:
            logger.warning("No content nodes returned from API")
            return {}

        # Transform to tree structure
        tree = _build_tree_structure(nodes)

        # Validate schema if requested
        if validate_schema and not _validate_tree_schema(tree):
            error_msg = "Generated tree structure does not match codemap schema"
            logger.error(error_msg)
            return {"error": error_msg}

        logger.info(f"Successfully transformed {len(nodes)} nodes into codemap tree")
        return tree

    except Exception as e:
        error_msg = f"Error fetching/transforming codemap: {e!s}"
        logger.error(error_msg)
        return {"error": error_msg}


def get_codemap_for_path(
    org_id: str, target_path: str, max_depth: int, version_id: str
) -> dict[str, Any] | dict[str, str]:
    """
    Get codemap for a specific path with depth limiting.

    Args:
        target_path: Target path to get codemap for
        max_depth: Maximum depth to traverse
        version_id: Version ID for the nodes

    Returns:
        Codemap tree structure or error response
    """
    # Normalize path filter
    if not target_path.endswith("%"):
        target_path = f"{target_path}%"

    # TODO: resolve path prefixing if needed
    # if not target_path.startswith(self.config.driver_docs_prefix):
    #     target_path = f"{self.config.driver_docs_prefix}{target_path}"

    # Get full codemap first
    full_tree = get_code_map(
        org_id=org_id,
        path_filter=target_path,
        version_id=version_id,
        max_depth=max_depth if max_depth > 0 else 5,
        validate_schema=True,
    )

    # Return error if present
    if isinstance(full_tree, dict) and "error" in full_tree:
        return full_tree

    # Apply depth limiting if needed
    # if max_depth > 0:
    #     limited_tree = self._limit_tree_depth(full_tree, max_depth)
    #     return limited_tree

    return full_tree


def main():
    # Example usage
    org_id = "org_s76pU1v8LAYhTOWB"
    target_path = "python-backend/"
    max_depth = 5
    version_id = "bb0745be-99b6-4f4b-aca3-f878c7afa135"

    codemap = get_codemap_for_path(
        org_id=org_id,
        target_path=target_path,
        max_depth=max_depth,
        version_id=version_id,
    )

    if isinstance(codemap, dict) and "error" in codemap:
        print(f"Error: {codemap['error']}")
    else:
        print("Codemap structure:")
        print(codemap)


if __name__ == "__main__":
    main()
