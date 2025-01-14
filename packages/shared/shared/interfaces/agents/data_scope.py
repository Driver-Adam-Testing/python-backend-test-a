from database.models_v2 import Node
from pydantic import BaseModel
from sqlmodel import Session, select


class DataScope(BaseModel):
    """
    Scope of the agent's operation.

    Attributes:
        nodes (List[Node]): List of nodes the agent can access.
        organization_id (str | None): The organization ID.
    """

    nodes: list[Node] = []

    def to_child_inclusive_nodes(self, session: Session) -> list[Node]:
        all_nodes = set(self.nodes)
        for node in self.nodes:
            child_nodes = session.exec(
                select(Node).where(
                    (Node.version_id == node.version_id)
                    & (Node.relative_path.startswith(node.relative_path))
                )
            ).all()
            all_nodes.update(child_nodes)
        return list(all_nodes)
