import copy
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
    status: NodeStatus = NodeStatus.UNMODIFIED

    def __hash__(self):
        return hash(self.root_rel_path) + hash(self.kind)

    def __str__(self) -> str:
        return f"{self.root_rel_path}"


@dataclass
class Node(LiteNode):
    parent: Optional["Node"] = None
    children: dict[str, "Node"] | None = field(default_factory=dict)

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
        """Yields all nodes upstream of this node, including itself."""
        current = self
        while current is not None:
            yield current
            current = current.parent

    def traverse_downstream(self) -> Generator["Node", None, None]:
        """Yields all downstream nodes, including itself."""
        yield self
        for child in self.children.values():
            yield from child.traverse_downstream()

    def into_lite_node(self) -> LiteNode:
        return LiteNode(
            kind=self.kind, root_rel_path=self.root_rel_path, status=self.status
        )

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
    node_rel_path_to_content_hash: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.root_abs_path.exists():
            raise FileNotFoundError(
                f"Codebase root path {self.root_abs_path} does not exist."
            )
        self.root = Node(kind=NodeKind.ROOT_FOLDER, root_rel_path=Path(""), parent=None)

    def add_file(
        self, path: Path, change_status=True, file_hash: str | None = None
    ) -> None:
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

        # If provided a hash for a file (leaf node), store it
        if file_hash:
            self.node_rel_path_to_content_hash[
                current.root_rel_path.as_posix()
            ] = file_hash

        # When a new node is added, ensure upstream nodes are correctly marked
        if node_added and change_status:
            for node in current.traverse_upstream():
                # Only mark as MODIFIED if the node already existed
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

    # TODO add tests for this!!
    def delete_file_node(self, path: Path) -> None:
        """Removes a file node from the DAG based on the given path.
        If a parent has no other children after deletion, recursively remove empty folders upstream."""
        relative_path = path.relative_to(self.root_abs_path)
        parts = relative_path.parts

        current = self.root
        current_path = Path("")
        parent = None

        # Traverse to the node to be deleted
        for part in parts:
            current_path /= part
            path_key = current_path.as_posix()
            if path_key in current.children:
                parent = current
                current = current.children[path_key]
            else:
                raise KeyError(f"Cannot delete. {path} not found in tree.")

        if current.kind != NodeKind.FILE:
            raise TypeError(
                f"Cannot delete {path}. Only file nodes can be deleted with this method."
            )

        # Remove the node from its parent
        if parent:
            parent.remove_child(current_path)
        else:
            raise ValueError("Cannot delete the root node.")

        self.node_rel_path_to_content_hash.pop(current.root_rel_path.as_posix(), None)
        self._remove_empty_parents(parent)

    def _remove_empty_parents(self, node: Node | None) -> None:
        """Recursively remove parent nodes if they have no children and are folders."""
        while node and node.kind in {NodeKind.SUB_FOLDER, NodeKind.ROOT_FOLDER}:
            if node.children:
                break
            if node.parent is None:
                break  # Stop if this is the root node
            parent = node.parent
            # Explicitly remove the empty folder node from its parent
            parent.remove_child(node.root_rel_path)
            node = parent

    def topological_sort(
        self,
        changed_nodes_only: bool = False,
        files_only: bool = False,
        folders_only: bool = False,
    ) -> list[Node]:
        sorter = graphlib.TopologicalSorter()

        def add_nodes_and_edges(node: Node):
            sorter.add(node)
            for child in node.children.values():
                sorter.add(node, child)
                add_nodes_and_edges(child)

        add_nodes_and_edges(self.root)
        sorted_nodes = list(sorter.static_order())

        if changed_nodes_only:
            sorted_nodes = [
                node for node in sorted_nodes if node.status != NodeStatus.UNMODIFIED
            ]
        if files_only:
            sorted_nodes = [node for node in sorted_nodes if node.kind == NodeKind.FILE]
        elif folders_only:
            sorted_nodes = [
                node
                for node in sorted_nodes
                if node.kind in (NodeKind.SUB_FOLDER, NodeKind.ROOT_FOLDER)
            ]

        return sorted_nodes

    def compute_diff(self, old: "FileTreeDag"):
        # This DAG has annotations of the changes required to go from `old` to `self` state
        diff_dag = copy.deepcopy(old)
        # We change the path to the root path of self so that the
        # resulting diff can be used to access the actual files from the new dag by the caller
        diff_dag.root_abs_path = self.root_abs_path

        def collect_nodes(dag: FileTreeDag) -> dict[str, Node]:
            nodes = {}
            for node in dag.root.traverse_downstream():
                nodes[node.root_rel_path.as_posix()] = node
            return nodes

        old_nodes = collect_nodes(old)
        self_nodes = collect_nodes(self)

        # Handle additions and mods
        for path, self_node in self_nodes.items():
            if path not in old_nodes:
                if self_node.kind == NodeKind.FILE:
                    # Change status implies we'll mark as added
                    diff_dag.add_file(diff_dag.root_abs_path / path, change_status=True)
            else:
                old_node = old_nodes[path]
                if self_node.kind != old_node.kind:
                    diff_dag.mark_as_modified(
                        diff_dag.root_abs_path / path, include_upstream=True
                    )
                elif (
                    self_node.kind == NodeKind.FILE
                    and self.node_rel_path_to_content_hash[path]
                    != old.node_rel_path_to_content_hash[
                        path
                    ]  # TODO diffing implies hash is *required*. is that correct?
                ):
                    diff_dag.mark_as_modified(
                        diff_dag.root_abs_path / path, include_upstream=True
                    )

        # Handle removals
        for path, old_node in old_nodes.items():
            # print(f"-> checking if {path} got removed")
            if path not in self_nodes and old_node.kind == NodeKind.FILE:
                # print(f"=> {path} got removed! calling delete node")
                diff_dag.delete_file_node(diff_dag.root_abs_path / path)

        return diff_dag

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
