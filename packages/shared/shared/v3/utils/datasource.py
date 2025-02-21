from __future__ import annotations

from uuid import UUID

from database.db import get_session
from database.models_v2 import Node, PrimaryAsset, Version
from pydantic import BaseModel, Field, PrivateAttr
from sqlalchemy.orm import selectinload
from sqlmodel import select


class DataSource(BaseModel):
    node_ids: list[UUID] = Field(default_factory=list)
    organization_id: str

    # Cache for the Node objects so we don't re-fetch on every property access
    _cached_nodes: list[Node] | None = PrivateAttr(default=None)

    @classmethod
    def from_node_ids(cls, node_ids: list[UUID], organization_id: str) -> DataSource:
        """
        Factory that constructs a DataSource directly from node_ids & organization_id.
        """
        return cls(node_ids=node_ids, organization_id=organization_id)

    @classmethod
    def from_page_id(cls, page_node_id: UUID, organization_id: str) -> DataSource:
        """
        Example of pulling node_ids from DocumentSource (legacy usage).
        """
        from database.models_v1 import DocumentSource

        with get_session() as session:
            document_sources = session.exec(
                select(DocumentSource).where(
                    DocumentSource.page_node_id == page_node_id
                )
            ).all()
            node_ids = [ds.source_node_id for ds in document_sources]
            return cls(node_ids=node_ids, organization_id=organization_id)

    @property
    def nodes(self) -> list[Node]:
        """
        Load Node objects for our node_ids, caching so we only do one DB query.
        """
        if self._cached_nodes is None:
            with get_session() as session:
                stmt = (
                    select(Node)
                    .join(Version)
                    .join(PrimaryAsset)
                    .where(PrimaryAsset.organization_id == self.organization_id)
                    .where(Node.id.in_(self.node_ids))
                    .options(selectinload(Node.version))
                )
                self._cached_nodes = session.exec(stmt).all()
        return self._cached_nodes

    def is_in_scope(self, child_path: str) -> bool:
        """
        Check if a given child_path is within the scope of the parent_path and if it has a parent node in the existing list of nodes.
        """
        for parent_node in self.nodes:
            parent_path = parent_node.relative_path.rstrip("/")
            if child_path.startswith(f"{parent_path}/"):
                return True

        return False

    def narrow(
        self,
        requested_paths: list[str],
    ) -> DataSource:
        """
        Given a list of relative_paths (e.g. "Marlin/Marlin/src/lcd/..."),
        produce a new DataSource that:

          1) Finds any Nodes in this scope whose `relative_path` exactly matches
             one of the `requested_paths`.
          2) Always includes all child nodes that share the same version_id and
             whose paths begin with that path (plus a slash).

        Example:
          If the user requests ["Marlin/Marlin/src/lcd"] and that Node's version_id
          is X, we query for all nodes with version_id == X and relative_path
          LIKE "Marlin/Marlin/src/lcd/%".
        """
        matched_nodes = []

        # Build a lookup by relative_path -> [Node, Node, ...]
        # (We might have multiple nodes with the same relative_path if they belong to different versions.)
        path_map: dict[str, list[Node]] = {}
        for node in self.nodes:
            path_map.setdefault(node.relative_path, []).append(node)

        # We will gather matches in this list
        all_matches: list[Node] = []

        with get_session() as session:
            for path in requested_paths:
                path = path.rstrip("/")

                # 1) Find all nodes in the current DataSource that have exactly that path
                direct_matches = path_map.get(path, [])
                for parent_node in direct_matches:
                    all_matches.append(parent_node)

                    # Always include subfolders
                    stmt_subfolders = (
                        select(Node)
                        .where(Node.version_id == parent_node.version_id)
                        .where(Node.relative_path.like(f"{path}%"))
                        .options(selectinload(Node.version))
                    )
                    child_nodes = session.exec(stmt_subfolders).all()
                    all_matches.extend(child_nodes)

        # Remove duplicates (in case multiple requested_paths overlap)
        unique_matches = list({n.id: n for n in all_matches}.values())

        # Build a new DataSource from these matches
        narrowed = DataSource(
            node_ids=[n.id for n in unique_matches],
            organization_id=self.organization_id,
        )
        narrowed._cached_nodes = unique_matches
        return narrowed

    def human_readable_summary(self) -> str:
        """
        Creates a simple summary of this DataSource by listing the relative_path
        of each node, sorted alphabetically.

        If you want more advanced grouping or multiple versions,
        you'd modify/expand this method.
        """
        paths = sorted({node.relative_path for node in self.nodes})
        lines = [f"- {p}" for p in paths]
        return "\n".join(lines)
