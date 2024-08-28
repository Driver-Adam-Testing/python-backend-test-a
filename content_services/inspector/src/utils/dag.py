import graphlib
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class NodeStatus(Enum):
    UNMODIFIED = 0
    MODIFIED = 1
    ADDED = 2
    REMOVED = 3

    def __str__(self) -> str:
        return self.name.lower()


class NodeKind(Enum):
    FILE = 0
    SUB_FOLDER = 1
    ROOT_FOLDER = 2

    def __str__(self) -> str:
        if self == NodeKind.FILE:
            return "file"
        elif self == NodeKind.SUB_FOLDER:
            return "folder"
        elif self == NodeKind.ROOT_FOLDER:
            return "root"
        else:
            raise ValueError("Unreachable")


@dataclass
class LiteNode:
    """Node that does not store children/parent info; easily serialized/deserialized"""

    kind: NodeKind
    root_rel_path: Path

    def __hash__(self):
        return hash(self.root_rel_path) + hash(self.kind)

    def __str__(self) -> str:
        return f"{self.root_rel_path}"


@dataclass
class Node(LiteNode):
    parent: Optional["Node"]
    children: dict[str, "Node"] | None = field(default_factory=dict)
    status: NodeStatus = NodeStatus.UNMODIFIED

    def add_child(self, child: "Node") -> None:
        self.children[child.root_rel_path.as_posix()] = child
        child.parent = self

    def remove_child(self, path: Path) -> None:
        child_key = path.as_posix()
        if child_key in self.children:
            child = self.children[child_key]
            child.parent = None
            del self.children[child_key]

    def traverse_upstream(self) -> Generator["Node", None, None]:
        """Yield all nodes upstream of this node, including itself."""
        current = self
        while current is not None:
            yield current
            current = current.parent

    def traverse_downstream(self) -> Generator["Node", None, None]:
        """Yield all downstream nodes, including itself."""
        yield self
        for child in self.children.values():
            yield from child.traverse_downstream()

    def into_lite_node(self) -> LiteNode:
        return LiteNode(kind=self.kind, root_rel_path=self.root_rel_path)

    def __str__(self) -> str:
        return f"{self.root_rel_path}({', '.join(self.children.keys())})"

    # TODO: this is funny because the node is not frozen in state.
    # Revisit this. Maybe we need a lite node that keeps its children?
    def __hash__(self):
        return super().__hash__()


@dataclass
class FileTreeDag:
    root: Node = field(init=False)
    root_abs_path: Path

    def __post_init__(self):
        if not self.root_abs_path.exists():
            raise FileNotFoundError(
                f"Codebase root path {self.root_abs_path} does not exist."
            )
        self.root = Node(kind=NodeKind.ROOT_FOLDER, root_rel_path=Path(""), parent=None)

    def add_file(self, path: Path, change_status=True) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist.")
        if not path.is_file():
            raise ValueError(f"Path {path} is not a file.")

        relative_path = path.relative_to(self.root_abs_path)
        parts = relative_path.parts

        current = self.root
        current_path = Path("")
        node_added = False

        for part in parts:
            current_path /= part
            current_full_path = self.root_abs_path / current_path
            path_key = current_path.as_posix()
            if path_key not in current.children:
                if current_full_path.is_file():
                    kind = NodeKind.FILE
                elif current_full_path.is_dir():
                    kind = NodeKind.SUB_FOLDER
                else:
                    raise ValueError(
                        f"Path {current_full_path} is neither a file nor a directory."
                    )

                new_node = Node(
                    root_rel_path=current_path,
                    kind=kind,
                    parent=current,
                    status=NodeStatus.ADDED if change_status else NodeStatus.UNMODIFIED,
                )
                current.add_child(new_node)
                node_added = True
                current = new_node
            else:
                current = current.children[path_key]
                # current.status = (
                #     NodeStatus.MODIFIED if change_status else NodeStatus.UNMODIFIED
                # )  # This is so that if we marked for deltion a node with a removal status, and then re-added it, it will be marked as modified

        # When a new node is added, ensure upstream nodes are correctly marked
        if node_added and change_status:
            for node in current.traverse_upstream():
                # Only mark as MODIFIED if the node was already existing
                if node.status == NodeStatus.UNMODIFIED:
                    node.status = NodeStatus.MODIFIED

    def mark_file_removal(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist.")
        if not path.is_file():
            raise ValueError(f"Path {path} is not a file.")

        relative_path = path.relative_to(self.root_abs_path)
        parts = relative_path.parts

        current = self.root
        current_path = Path("")
        for part in parts:
            current_path /= part
            path_key = current_path.as_posix()
            try:
                current = current.children[path_key]
            except KeyError as e:
                raise KeyError(f"Cannot remove. {path} not found in tree.") from e

        # Before removing, mark upstream nodes as MODIFIED
        for node in current.traverse_upstream():
            if node != current:
                node.status = NodeStatus.MODIFIED

        if current.parent:
            current.status = (
                NodeStatus.REMOVED
            )  # Mark for removal, without actually removing it
            self._propagate_removal_upstream(current.parent)
            # current.parent.remove_child(current.root_rel_path)

    def _propagate_removal_upstream(self, node: Node) -> None:
        # Mark parent nodes as removed if they have no other active children
        while node:
            if node.parent is None:
                break  # Stop at the root, don't mark or remove the root
            all_removed = all(
                child.status == NodeStatus.REMOVED for child in node.children.values()
            )
            if all_removed:
                node.status = NodeStatus.REMOVED
            else:
                break  # Stop marking as removed if there are active children
            node = node.parent

    def mark_as_modified(
        self,
        path: Path,
        include_upstream: bool = True,
        include_downstream: bool = False,
    ) -> None:
        relative_path = path.relative_to(self.root_abs_path)
        parts = relative_path.parts

        current = self.root
        current_path = Path("")
        for part in parts:
            current_path /= part
            path_key = current_path.as_posix()
            if path_key not in current.children:
                raise KeyError(f"Cannot mark as modified. {path} not found in tree.")
            current = current.children[path_key]

        current.status = NodeStatus.MODIFIED

        if include_upstream:
            for node in current.traverse_upstream():
                node.status = NodeStatus.MODIFIED

        if include_downstream:
            for node in current.traverse_downstream():
                node.status = NodeStatus.MODIFIED

    def topological_sort(
        self,
        changed_nodes_only: bool = False,
        files_only: bool = False,
        folders_only: bool = False,
    ) -> list[Node]:
        sorter = graphlib.TopologicalSorter()

        def add_nodes_and_edges(node: Node):
            # Only add nodes that are modified or added, if the flag is set
            if not changed_nodes_only or node.status != NodeStatus.UNMODIFIED:
                for child in node.children.values():
                    # Recursively add children if they are also modified or added
                    if not changed_nodes_only or child.status != NodeStatus.UNMODIFIED:
                        sorter.add(node, child)
                    add_nodes_and_edges(child)

        add_nodes_and_edges(self.root)
        sorted_nodes = list(sorter.static_order())
        if files_only:
            sorted_nodes = [node for node in sorted_nodes if node.kind == NodeKind.FILE]
        if folders_only:
            sorted_nodes = [
                node
                for node in sorted_nodes
                if node.kind in (NodeKind.SUB_FOLDER, NodeKind.ROOT_FOLDER)
            ]

        return sorted_nodes

    # def render_graph(self, path=Path("out.pdf")) -> None:
    #     from graphviz import Digraph
    #
    #     dot = Digraph(comment="FileTreeDAG")
    #
    #     status_colors = {
    #         NodeStatus.UNMODIFIED: "grey",
    #         NodeStatus.MODIFIED: "yellow",
    #         NodeStatus.ADDED: "green",
    #         NodeStatus.REMOVED: "red",
    #     }
    #
    #     def add_nodes_and_edges(node: Node):
    #         node_color = status_colors.get(node.status, "lightgrey")
    #         node_shape = "box" if node.kind == NodeKind.FILE else "ellipse"
    #
    #         node_label = f"{node.root_rel_path} ({node.status.name})"
    #         dot.node(
    #             node.root_rel_path.as_posix(),
    #             label=node_label,
    #             style="filled",
    #             color=node_color,
    #             shape=node_shape,
    #         )
    #
    #         for child in node.children.values():
    #             dot.edge(node.root_rel_path.as_posix(), child.root_rel_path.as_posix())
    #             add_nodes_and_edges(child)
    #
    #     # Start from the root and add all nodes
    #     add_nodes_and_edges(self.root)
    #
    #     dot.render(str(path.absolute()), format="pdf", view=False)

    def __str__(self):
        return str(self.root)
