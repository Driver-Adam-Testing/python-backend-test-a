from uuid import UUID

from database.db import get_session
from database.models import Node, PrimaryAsset, Version
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import and_, or_, select


# TODO: from_node_ids?
# TODO: Validate organization_id
class DataScope(BaseModel):
    """
    Scope of the agent's operation.

    Attributes:
        nodes (List[DataScopeNode]): List of nodes the agent can access.
        organization_id (str | None): The organization ID.
    """

    class DataScopeNode:
        """
        Represents a node within the DataScope that is lazy-loaded from the database.
        """

        def __init__(self, node: Node) -> None:
            self._node = node

        @property
        def node(self) -> Node:
            return self._node

        def get_identifier(self) -> str:
            """
            Returns a string identifier for the node in the format: {version_display_name}/{relative_path}.
            """
            version_display_name = (
                self._node.version.vcs_hash
                if self._node.version.vcs_hash
                else "Unversioned"
            )
            return f"{version_display_name}/{self._node.relative_path}"

    node_ids: list[UUID]

    # TODO: Move user_id somewhere else
    user_id: str
    organization_id: str
    _cached_nodes: list[DataScopeNode] | None = None

    @property
    def nodes(self) -> list[DataScopeNode]:
        if self._cached_nodes is None:
            with get_session() as session:
                stmt = (
                    select(Node)
                    .options(
                        selectinload(Node.version).selectinload(Version.primary_asset)
                    )
                    .where(Node.id.in_(self.node_ids))
                )
                nodes = session.exec(stmt).all()
            self._cached_nodes = [DataScope.DataScopeNode(node) for node in nodes]
        return list(self._cached_nodes)

    def get_node_by_identifier(self, identifier: str) -> DataScopeNode | None:
        """
        Retrieves a node by its identifier in the format: {version_display_name}/{relative_path}.
        """
        for data_scope_node in self.nodes:
            if data_scope_node.get_identifier() == identifier:
                return data_scope_node
        return None

    def to_child_datascope(self, identifiers: list[str]) -> "DataScope":
        """
        This returns a DataScope that has node_ids of Nodes where the version display name and the relative_path are children of the in this datascope, and errors if false.
        """

        # Ensure all identifiers start with an existing node identifier
        existing_identifiers = {node.get_identifier() for node in self.nodes}
        for identifier in identifiers:
            if not any(
                identifier.startswith(existing_id)
                for existing_id in existing_identifiers
            ):
                raise ValueError(
                    f"Identifier '{identifier}' does not start with any existing node identifier."
                )

        # Get node_ids that match a node on this datascope
        matching_node_ids = []
        for identifier in identifiers:
            node = self.get_node_by_identifier(identifier)
            if node:
                matching_node_ids.append(node.node.id)

        if len(matching_node_ids) != len(identifiers):
            with get_session() as session:
                stmt = (
                    select(Node)
                    .join(Version)
                    .join(PrimaryAsset)
                    .options(
                        selectinload(Node.version).selectinload(Version.primary_asset)
                    )
                    .where(
                        or_(
                            *[
                                and_(
                                    or_(
                                        Node.relative_path
                                        == identifier.split("/", 1)[1],
                                        Node.relative_path
                                        == identifier.split("/", 1)[1] + "/",
                                    ),
                                    or_(
                                        # TODO: are datascopes still needed?
                                        # TODO: if so, unsure how to approach this query
                                        Version.vcs_hash == identifier.split("/", 1)[0],
                                        Version.vcs_hash == None,  # noqa: E711
                                    ),
                                )
                                for identifier in identifiers
                            ]
                        )
                    )
                    .where(PrimaryAsset.organization_id == self.organization_id)
                )
                nodes = session.exec(stmt).all()
                ds = DataScope(
                    node_ids=[n.id for n in nodes],
                    user_id=self.user_id,
                    organization_id=self.organization_id,
                )
                return ds
        else:
            ds = DataScope(
                node_ids=matching_node_ids,
                user_id=self.user_id,
                organization_id=self.organization_id,
            )
            ds._cached_nodes = [
                node for node in self.nodes if node.node.id in matching_node_ids
            ]
            return ds

    def to_human_readable_summary(self) -> str:
        # Create a dictionary to group identifiers by their primary asset display name
        grouped_identifiers = {}

        for node in self.nodes:
            primary_asset_display_name = node.node.version.primary_asset.display_name
            version_display_name = (
                node.node.version.vcs_hash
                if node.node.version.vcs_hash
                else "Unversioned"
            )
            identifier = f"{version_display_name}/{node.node.relative_path}"

            if primary_asset_display_name not in grouped_identifiers:
                grouped_identifiers[primary_asset_display_name] = []

            grouped_identifiers[primary_asset_display_name].append(identifier)

        # Format the grouped identifiers into a human-readable summary
        summary_lines = []
        for primary_asset, identifiers in grouped_identifiers.items():
            summary_lines.append(f"Paths for Asset: {primary_asset}")
            for identifier in identifiers:
                summary_lines.append(f"  - {identifier}")

        return "\n".join(summary_lines)
