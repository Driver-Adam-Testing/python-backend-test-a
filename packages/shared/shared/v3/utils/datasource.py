from __future__ import annotations

from typing import TYPE_CHECKING

from database.db import get_session
from database.models_v2 import Node, PrimaryAsset, Version
from pydantic import BaseModel, Field, PrivateAttr
from sqlalchemy.orm import selectinload
from sqlmodel import select

if TYPE_CHECKING:
    from uuid import UUID


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
        with get_session() as session:
            nodes = session.exec(
                select(Node)
                .join(Version, Node.version_id == Version.id)
                .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
                .where(PrimaryAsset.organization_id == organization_id)
                .where(Node.id.in_(node_ids))
            ).all()
            if len(nodes) != len(node_ids):
                raise ValueError(
                    f"Some nodes were not found for the given node_ids: {node_ids}"
                )

            datasource = cls(
                node_ids=[n.id for n in nodes], organization_id=organization_id
            )
            datasource._cached_nodes = nodes
            return datasource

    @classmethod
    def from_page_id(cls, page_node_id: UUID, organization_id: str) -> DataSource:
        """
        Example of pulling node_ids from DocumentSource (legacy usage).
        """
        from database.models_v1 import DocumentSource

        with get_session() as session:
            nodes = session.exec(
                select(Node)
                .join(DocumentSource, Node.id == DocumentSource.source_node_id)
                .join(Version, Node.version_id == Version.id)
                .join(PrimaryAsset, Version.primary_asset_id == PrimaryAsset.id)
                .where(PrimaryAsset.organization_id == organization_id)
                .where(DocumentSource.page_node_id == page_node_id)
            ).all()
            datasource = cls(
                node_ids=[n.id for n in nodes], organization_id=organization_id
            )
            datasource._cached_nodes = nodes
            return datasource

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
