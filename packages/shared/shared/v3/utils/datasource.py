import uuid
from collections import defaultdict

from database.db import get_session
from database.models_v1 import DocumentSource
from database.models_v2 import Node, PrimaryAsset, Version
from database.models_v2_enums import NodeKind
from pydantic import BaseModel, Field, PrivateAttr
from sqlalchemy.orm import selectinload
from sqlmodel import and_, or_, select


class DataSource(BaseModel):
    """
    A DataSource represents a set of node_ids that belong to a single organization.
    It also provides an optional cache of the underlying Node objects.
    """

    node_ids: list[uuid.UUID] = Field(default_factory=list)
    organization_id: str

    # Cache for the Node objects so we don't re-fetch on every property access
    _cached_nodes: list[Node] | None = PrivateAttr(default=None)

    def __init__(self, node_ids: list[uuid.UUID], organization_id: str) -> None:
        """
        Initialize the DataSource.

        Validates that all given node_ids belong to the specified organization_id.
        Raises:
            ValueError: If any node_id does not match the given organization_id.
        """
        super().__init__(node_ids=node_ids, organization_id=organization_id)

        if self.node_ids:
            with get_session() as session:
                stmt = (
                    select(Node.id)
                    .join(Version, Node.version_id == Version.id)
                    .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
                    .where(PrimaryAsset.organization_id == self.organization_id)
                    .where(Node.id.in_(self.node_ids))
                )
                matching_ids = session.exec(stmt).all()
                if len(matching_ids) != len(self.node_ids):
                    raise ValueError(
                        "Some node_ids do not match the given organization_id."
                    )

        self._cached_nodes = None

    @classmethod
    def from_node_ids(
        cls, node_ids: list[uuid.UUID], organization_id: str
    ) -> "DataSource":
        """
        Factory that constructs a DataSource directly from node_ids & organization_id.
        """
        datasource = cls(node_ids=node_ids, organization_id=organization_id)
        return datasource

    @classmethod
    def from_page_id(
        cls, page_node_id: uuid.UUID, organization_id: str
    ) -> "DataSource":
        """
        Example of pulling node_ids from DocumentSource (legacy usage).
        """

        with get_session() as session:
            stmt = select(DocumentSource).where(
                DocumentSource.page_node_id == page_node_id
            )
            document_sources = session.exec(stmt).all()
            node_ids = [ds.source_node_id for ds in document_sources]

            datasource = cls(node_ids=node_ids, organization_id=organization_id)
            return datasource

    @property
    def nodes(self) -> list[Node]:
        """
        Returns the list of cached Node objects, loading them if necessary.
        """
        if self._cached_nodes is None:
            with get_session() as session:
                # Load all ancestors in a single query
                ancestors = session.exec(
                    select(Node)
                    .options(selectinload(Node.version))
                    .where(Node.id.in_(self.node_ids))
                ).all()

                # Build a set of conditions for any ancestor's version/path
                conditions = []
                for anc in ancestors:
                    conditions.append(
                        and_(
                            Node.version_id == anc.version_id,
                            Node.depth > anc.depth,
                            Node.relative_path.startswith(anc.relative_path),
                        )
                    )

                # Query descendants in one shot using OR across all conditions
                if conditions:
                    descendants_stmt = select(Node).where(or_(*conditions))
                    descendants = session.exec(descendants_stmt).all()
                else:
                    descendants = []

                id_to_node = {}
                for node in ancestors + descendants:
                    id_to_node[node.id] = node
                self._cached_nodes = list(id_to_node.values())
        return self._cached_nodes

    def describe_contents_char_limit(self, char_limit: int) -> str:
        """
        Describes the contents of this DataSource by grouping nodes by version,
        and limiting how many folders deep we go (tree_depth). If tree_depth is None,
        no limit is applied.
        """
        description = ""
        tree_depth = 2
        while True:
            new_description = self.describe_contents(tree_depth=tree_depth)
            if description == new_description:
                break
            if len(new_description) <= char_limit:
                description = new_description
            else:
                break
            tree_depth += 1
        return description

    def describe_contents(self, tree_depth: int | None = None) -> str:
        """
        Describes the contents of this DataSource by grouping nodes by version,
        and limiting how many folders deep we go (tree_depth). If tree_depth is None,
        no limit is applied.
        """
        summary_lines = []

        def build_tree(nodes: list[Node]) -> dict:
            built_tree = {"children": {}, "files": []}
            for node in nodes:
                parts = node.relative_path.strip("/").split("/")
                current = built_tree
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        if node.kind == NodeKind.CODEBASE_DIRECTORY:
                            current.setdefault("children", {})
                            if part not in current["children"]:
                                current["children"][part] = {
                                    "node": node,
                                    "children": {},
                                    "files": [],
                                }
                            else:
                                current["children"][part]["node"] = node
                        else:
                            current.setdefault("files", []).append((part, node))
                    else:
                        current.setdefault("children", {})
                        if part not in current["children"]:
                            current["children"][part] = {
                                "node": None,
                                "children": {},
                                "files": [],
                            }
                        current = current["children"][part]
            return built_tree

        def count_files(tree_data: dict) -> int:
            """Recursively count all file nodes in the tree."""
            count = len(tree_data.get("files", []))
            for child in tree_data.get("children", {}).values():
                count += count_files(child)
            return count

        def traverse_tree(tree_data: dict, indent: int) -> None:
            # List all files at this level.
            files_here = sorted(fname for fname, _ in tree_data.get("files", []))
            if files_here:
                summary_lines.append("  " * indent + ", ".join(files_here))
            # Process each subfolder.
            for folder_name, folder_value in sorted(
                tree_data.get("children", {}).items()
            ):
                # If we've reached the depth limit, show a truncated view.
                if tree_depth is not None and (indent + 1) >= tree_depth:
                    file_count = count_files(folder_value)
                    summary_lines.append(
                        "  " * indent + f"{folder_name}/... ({file_count} files)"
                    )
                else:
                    file_count = count_files(folder_value)
                    summary_lines.append("  " * indent + f"{folder_name}/")

                    # Recurse into the folder.
                    traverse_tree(folder_value, indent + 1)

        # Group nodes by version to avoid mixing versions.

        version_groups = defaultdict(list)
        for node in self.nodes:
            version_groups[node.version_id].append(node)

        # Build summary for each version.
        for version_id, grouped_nodes in sorted(
            version_groups.items(), key=lambda x: str(x[0])
        ):
            summary_lines.append(f"Version: {str(version_id)[:8]} ...")
            built_tree = build_tree(grouped_nodes)
            traverse_tree(built_tree, indent=1)

        return "\n".join(summary_lines)
