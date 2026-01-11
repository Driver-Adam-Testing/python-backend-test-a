import uuid
from collections import defaultdict

from database.db import get_session
from database.models import DocumentSource, Node, PrimaryAsset, Version, VersionNode
from database.models_enums import NodeKind
from pydantic import BaseModel, Field, PrivateAttr
from shared.authorization.query_filters import primary_asset_grant_filter
from sqlalchemy.orm import selectinload
from sqlmodel import and_, or_, select


class DataSource(BaseModel):
    """
    A DataSource represents a set of version_node_ids that belong to a single organization and are accessible by the user.
    It also provides an optional cache of the underlying VersionNode objects and their associated Nodes.
    """

    version_node_ids: list[uuid.UUID] = Field(default_factory=list)
    organization_id: str
    user_id: str

    # Cache for the VersionNode objects so we don't re-fetch on every property access
    _cached_version_nodes: list[VersionNode] | None = PrivateAttr(default=None)

    def __init__(
        self, version_node_ids: list[uuid.UUID], organization_id: str, user_id: str
    ) -> None:
        """
        Initialize the DataSource.

        Validates that all given version_node_ids belong to the specified organization_id and are accessible by the user.
        Raises:
            ValueError: If any version_node_id does not match the given organization_id.
        """
        super().__init__(
            version_node_ids=version_node_ids,
            organization_id=organization_id,
            user_id=user_id,
        )

        version_node_pairs = []
        if self.version_node_ids:
            with get_session() as session:
                # Validate nodes belong to org AND user has access
                stmt = (
                    select(VersionNode.id)
                    .join(Version, VersionNode.version_id == Version.id)
                    .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
                    .where(PrimaryAsset.organization_id == self.organization_id)
                    .where(VersionNode.id.in_(self.version_node_ids))
                    .where(
                        primary_asset_grant_filter(
                            session, self.user_id, self.organization_id
                        )
                    )
                )
                matching_ids = session.exec(stmt).all()
                if len(matching_ids) != len(self.version_node_ids):
                    raise ValueError(
                        "Some version_node_ids do not match the given organization_id or user does not have access to all the associated assets."
                    )

                # Get VersionNode and Node data for _calculate_is_tuned
                stmt = (
                    select(VersionNode, Node)
                    .join(Node, VersionNode.node_id == Node.id)
                    .where(VersionNode.id.in_(self.version_node_ids))
                )
                version_node_pairs = session.exec(stmt).all()

        self._cached_version_nodes = None
        self._is_tuned = self._calculate_is_tuned(version_node_pairs)

    @staticmethod
    def _calculate_is_tuned(version_node_pairs: list[tuple[VersionNode, Node]]) -> bool:
        for version_node, node in version_node_pairs:
            if node.kind == NodeKind.CODEBASE_DIRECTORY and version_node.depth == 1:
                # node is a root level directory (depth 1)
                pass

            elif (
                node.kind == NodeKind.OTHER
                and version_node.relative_path.lower().endswith("pdf")
            ):
                # node is a PDF file
                pass
            else:
                # node is a file or subdirectory
                return True

        return False

    @classmethod
    def from_version_node_ids(
        cls, version_node_ids: list[uuid.UUID], organization_id: str, user_id: str
    ) -> "DataSource":
        """
        Factory that constructs a DataSource directly from version_node_ids, organization_id and user_id.
        """
        datasource = cls(
            version_node_ids=version_node_ids,
            organization_id=organization_id,
            user_id=user_id,
        )
        return datasource

    @classmethod
    def from_page_id(
        cls, page_version_node_id: uuid.UUID, organization_id: str, user_id: str
    ) -> "DataSource":
        """
        Factory that constructs a DataSource from DocumentSource entries linked to a page.
        """

        with get_session() as session:
            stmt = select(DocumentSource).where(
                DocumentSource.page_version_node_id == page_version_node_id
            )
            document_sources = session.exec(stmt).all()
            version_node_ids = [ds.source_version_node_id for ds in document_sources]

            datasource = cls(
                version_node_ids=version_node_ids,
                organization_id=organization_id,
                user_id=user_id,
            )
            return datasource

    @property
    def version_nodes(self) -> list[VersionNode]:
        """
        Returns the list of cached VersionNode objects plus all their descendants, loading them if necessary.
        Only returns version nodes the user is authorized to access.
        """
        if self._cached_version_nodes is None:
            with get_session() as session:
                # Load all ancestor VersionNodes with authorization check
                ancestor_version_nodes = session.exec(
                    select(VersionNode)
                    .options(selectinload(VersionNode.node))
                    .join(Version, VersionNode.version_id == Version.id)
                    .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
                    .where(VersionNode.id.in_(self.version_node_ids))
                    .where(
                        primary_asset_grant_filter(
                            session, self.user_id, self.organization_id
                        )
                    )
                ).all()

                # Build a set of conditions for any ancestor's version/path
                conditions = []
                for anc_vn in ancestor_version_nodes:
                    conditions.append(
                        and_(
                            VersionNode.version_id == anc_vn.version_id,
                            VersionNode.depth > anc_vn.depth,
                            VersionNode.relative_path.startswith(anc_vn.relative_path),
                        )
                    )

                # Query descendant VersionNodes with authorization check
                if conditions:
                    descendant_version_nodes_stmt = (
                        select(VersionNode)
                        .options(selectinload(VersionNode.node))
                        .join(Version, VersionNode.version_id == Version.id)
                        .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
                        .where(or_(*conditions))
                        .where(
                            primary_asset_grant_filter(
                                session, self.user_id, self.organization_id
                            )
                        )
                    )
                    descendant_version_nodes = session.exec(
                        descendant_version_nodes_stmt
                    ).all()
                else:
                    descendant_version_nodes = []

                # Combine and deduplicate VersionNodes
                id_to_version_node = {
                    vn.id: vn
                    for vn in ancestor_version_nodes + descendant_version_nodes
                }
                self._cached_version_nodes = list(id_to_version_node.values())
        return self._cached_version_nodes

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

        def build_tree(version_nodes: list[VersionNode]) -> dict:
            built_tree = {"children": {}, "files": []}
            for vn in version_nodes:
                parts = vn.relative_path.strip("/").split("/")
                current = built_tree
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        if vn.node and vn.node.kind == NodeKind.CODEBASE_DIRECTORY:
                            current.setdefault("children", {})
                            if part not in current["children"]:
                                current["children"][part] = {
                                    "node": vn.node,
                                    "children": {},
                                    "files": [],
                                }
                            else:
                                current["children"][part]["node"] = vn.node
                        else:
                            current.setdefault("files", []).append((part, vn.node))
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

        # Group version nodes by version to avoid mixing versions.

        version_groups = defaultdict(list)
        for vn in self.version_nodes:
            version_groups[vn.version_id].append(vn)

        # Build summary for each version.
        for version_id, grouped_version_nodes in sorted(
            version_groups.items(), key=lambda x: str(x[0])
        ):
            summary_lines.append(
                f"Tuned = {self._is_tuned}\nVersion: {str(version_id)[:8]} ..."
            )
            built_tree = build_tree(grouped_version_nodes)
            traverse_tree(built_tree, indent=1)

        return "\n".join(summary_lines)
