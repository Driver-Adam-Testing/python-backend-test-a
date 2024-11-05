import subprocess
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from .dag import FileTreeDag, LiteNode, Node, NodeKind, NodeStatus


class TestNode:
    @pytest.fixture
    def root_node(self) -> Node:
        return Node(
            kind=NodeKind.ROOT_FOLDER,
            root_rel_path=Path("/"),
            parent=None,
            status=NodeStatus.UNMODIFIED,
        )

    @pytest.fixture
    def child_node(self) -> Node:
        return Node(
            kind=NodeKind.SUB_FOLDER,
            root_rel_path=Path("/child"),
            parent=None,
            status=NodeStatus.UNMODIFIED,
        )

    @pytest.fixture
    def second_child_node(self) -> Node:
        return Node(
            kind=NodeKind.SUB_FOLDER,
            root_rel_path=Path("/child2"),
            parent=None,
            status=NodeStatus.UNMODIFIED,
        )

    @pytest.fixture
    def grandchild_node(self) -> Node:
        return Node(
            kind=NodeKind.FILE,
            root_rel_path=Path("/child/grandchild"),
            parent=None,
            status=NodeStatus.UNMODIFIED,
        )

    def test_add_child(
        self, root_node: Node, child_node: Node, grandchild_node: Node
    ) -> None:
        root_node.add_child(child_node)
        assert child_node.parent == root_node
        assert root_node.children["/child"] == child_node

        child_node.add_child(grandchild_node)
        assert grandchild_node.parent == child_node
        assert child_node.children["/child/grandchild"] == grandchild_node
        assert grandchild_node.root_rel_path == Path("/child/grandchild")

    def test_remove_child(
        self, root_node: Node, child_node: Node, grandchild_node: Node
    ) -> None:
        root_node.add_child(child_node)
        child_node.add_child(grandchild_node)

        root_node.remove_child(Path("/child"))
        assert Path("/child") not in root_node.children
        assert child_node.parent is None

    def test_traverse_upstream(
        self, grandchild_node: Node, child_node: Node, root_node: Node
    ) -> None:
        root_node.add_child(child_node)
        child_node.add_child(grandchild_node)

        upstream_nodes = list(grandchild_node.traverse_upstream())
        assert upstream_nodes == [grandchild_node, child_node, root_node]

    def test_traverse_downstream(
        self,
        grandchild_node: Node,
        child_node: Node,
        second_child_node: Node,
        root_node: Node,
    ) -> None:
        root_node.add_child(child_node)
        root_node.add_child(second_child_node)
        child_node.add_child(grandchild_node)

        downstream_nodes = list(root_node.traverse_downstream())
        assert downstream_nodes == [
            root_node,
            child_node,
            grandchild_node,
            second_child_node,
        ]

        downstream_nodes_from_child = list(child_node.traverse_downstream())
        assert downstream_nodes_from_child == [child_node, grandchild_node]

        downstream_nodes_from_child = list(second_child_node.traverse_downstream())
        assert downstream_nodes_from_child == [second_child_node]

    def test_into_lite_node(self, grandchild_node: Node) -> None:
        lite_node = grandchild_node.into_lite_node()
        assert isinstance(lite_node, LiteNode)
        assert lite_node.kind == grandchild_node.kind
        assert lite_node.root_rel_path == grandchild_node.root_rel_path


def create_file_tree_dag(
    root_path: Path, structure: dict[str, str | None]
) -> FileTreeDag:
    """
    Creates a FileTreeDag with the given structure and file hashes.
    :param root_path: Root path for the DAG.
    :param structure: A dictionary where keys are relative paths, values are tuples of (NodeKind, hash or None).
    :return: A FileTreeDag instance.
    """
    root_path.mkdir()
    dag = FileTreeDag(root_abs_path=root_path)
    for path_str, file_hash in structure.items():
        path = root_path / path_str
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        dag.add_file(path, change_status=False, file_hash=file_hash)
    return dag


def run_tree_command(directory: Path) -> None:
    result = subprocess.run(
        ["tree", str(directory)],
        capture_output=True,
        text=True,
        check=True,
    )

    print(result.stdout)


class TestFileTreeDag:
    @pytest.fixture
    def temp_dir(self) -> Iterator[Path]:
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def setup_file_tree(
        self, temp_dir: Path
    ) -> tuple[Path, Path, Path, Path, Path, Path]:
        root_abs_path = temp_dir / "root"
        root_abs_path.mkdir()
        folder1 = temp_dir / "root" / "folder1"
        test_file0 = folder1 / "file0.txt"
        subfolder1 = folder1 / "subfolder1"
        test_file1 = subfolder1 / "file1.txt"
        test_file2 = subfolder1 / "file2.txt"
        subfolder1.mkdir(parents=True, exist_ok=True)
        test_file0.touch()
        test_file1.touch()
        test_file2.touch()
        return root_abs_path, test_file0, test_file1, test_file2, folder1, subfolder1

    def test_add_file_marks_ancestors_as_added(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=True)
        file_tree_dag.add_file(test_file1, change_status=True)
        file_tree_dag.add_file(test_file2, change_status=True)

        # Verify that the file is added and all ancestors are marked as added (except for root,
        # which gets marked as modified by convention)
        assert file_tree_dag.root.status == NodeStatus.MODIFIED
        assert file_tree_dag.root.children["folder1"].status == NodeStatus.ADDED
        assert (
            file_tree_dag.root.children["folder1"].children["folder1/subfolder1"].status
            == NodeStatus.ADDED
        )
        assert (
            file_tree_dag.root.children["folder1"].children["folder1/file0.txt"].status
            == NodeStatus.ADDED
        )
        assert (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file1.txt"]
            .status
            == NodeStatus.ADDED
        )

    def test_remove_file_marks_parents_as_modified(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=True)
        file_tree_dag.add_file(test_file1, change_status=True)
        file_tree_dag.add_file(test_file2, change_status=True)

        file_tree_dag.mark_file_removal(test_file1)

        # Verify that the file is marked for removal and its parent are marked as modified
        assert file_tree_dag.root.children["folder1"].status == NodeStatus.MODIFIED
        assert (
            file_tree_dag.root.children["folder1"].children["folder1/subfolder1"].status
            == NodeStatus.MODIFIED
        )

        file1_status = (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file1.txt"]
            .status
        )
        assert file1_status == NodeStatus.REMOVED

    def test_remove_file_marks_ancestors_as_removed_if_no_active_children(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, _, test_file1, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file1, change_status=True)

        file_tree_dag.mark_file_removal(test_file1)

        # Verify that all ancestors (except root) are marked as removed if they have no other active children
        assert (
            file_tree_dag.root.children["folder1"].children["folder1/subfolder1"].status
            == NodeStatus.REMOVED
        )
        assert file_tree_dag.root.children["folder1"].status == NodeStatus.REMOVED
        assert (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file1.txt"]
            .status
            == NodeStatus.REMOVED
        )

    def test_remove_file_does_not_mark_ancestors_as_removed_if_active_children_exist(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=True)
        file_tree_dag.add_file(test_file1, change_status=True)
        file_tree_dag.add_file(test_file2, change_status=True)

        file_tree_dag.mark_file_removal(test_file1)

        assert (
            file_tree_dag.root.children["folder1"].children["folder1/subfolder1"].status
            == NodeStatus.MODIFIED
        )
        assert (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file1.txt"]
            .status
            == NodeStatus.REMOVED
        )
        assert (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file2.txt"]
            .status
            == NodeStatus.ADDED
        )

    def test_mark_as_modified_propagates_to_parents(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=False)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        file_tree_dag.mark_as_modified(
            test_file1, include_upstream=True, include_downstream=False
        )

        # Verify that the file and its ancestors are marked as modified
        assert file_tree_dag.root.children["folder1"].status == NodeStatus.MODIFIED
        assert (
            file_tree_dag.root.children["folder1"].children["folder1/subfolder1"].status
            == NodeStatus.MODIFIED
        )
        assert (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file1.txt"]
            .status
            == NodeStatus.MODIFIED
        )

    def test_mark_as_modified_propagates_to_children(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        (
            root_abs_path,
            test_file0,
            test_file1,
            test_file2,
            folder1,
            subfolder1,
        ) = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=False)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        file_tree_dag.mark_as_modified(
            folder1, include_upstream=False, include_downstream=True
        )

        assert file_tree_dag.root.children["folder1"].status == NodeStatus.MODIFIED
        assert (
            file_tree_dag.root.children["folder1"].children["folder1/subfolder1"].status
            == NodeStatus.MODIFIED
        )
        assert (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file1.txt"]
            .status
            == NodeStatus.MODIFIED
        )
        assert (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file2.txt"]
            .status
            == NodeStatus.MODIFIED
        )

    def test_mark_as_modified_does_not_propagate_to_unchanged_ancestors_if_disabled(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=False)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        file_tree_dag.mark_as_modified(
            test_file1, include_upstream=False, include_downstream=False
        )

        assert file_tree_dag.root.children["folder1"].status == NodeStatus.UNMODIFIED
        assert (
            file_tree_dag.root.children["folder1"].children["folder1/subfolder1"].status
            == NodeStatus.UNMODIFIED
        )
        assert (
            file_tree_dag.root.children["folder1"]
            .children["folder1/subfolder1"]
            .children["folder1/subfolder1/file1.txt"]
            .status
            == NodeStatus.MODIFIED
        )

    def test_topological_sort_all_nodes(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        sorted_nodes = file_tree_dag.topological_sort()

        assert len(sorted_nodes) == 5
        assert sorted_nodes[0].root_rel_path in {
            Path("folder1/subfolder1/file1.txt"),
            Path("folder1/subfolder1/file2.txt"),
        }
        assert sorted_nodes[1].root_rel_path in {
            Path("folder1/subfolder1/file1.txt"),
            Path("folder1/subfolder1/file2.txt"),
        }
        assert sorted_nodes[2].root_rel_path == Path("folder1/subfolder1")
        assert sorted_nodes[3].root_rel_path == Path("folder1")
        assert sorted_nodes[4].root_rel_path == Path("")

    def test_topological_sort_changed_nodes_only(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        file_tree_dag.mark_file_removal(test_file1)
        sorted_nodes = file_tree_dag.topological_sort(changed_nodes_only=True)

        assert len(sorted_nodes) == 4
        assert sorted_nodes[0].root_rel_path == Path("folder1/subfolder1/file1.txt")
        assert sorted_nodes[1].root_rel_path == Path("folder1/subfolder1")
        assert sorted_nodes[2].root_rel_path == Path("folder1")
        assert sorted_nodes[3].root_rel_path == Path("")

    def test_mark_downstream_only_and_sort_changed_nodes(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        (
            root_abs_path,
            test_file0,
            test_file1,
            test_file2,
            folder1,
            subfolder1,
        ) = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)

        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        file_tree_dag.mark_as_modified(
            folder1, include_upstream=False, include_downstream=True
        )

        sorted_nodes = file_tree_dag.topological_sort(changed_nodes_only=True)
        for node in sorted_nodes:
            print(node)

        assert len(sorted_nodes) == 4

        sorted_paths = [node.root_rel_path for node in sorted_nodes]

        expected_paths = {
            Path("folder1"),
            Path("folder1/subfolder1"),
            Path("folder1/subfolder1/file1.txt"),
            Path("folder1/subfolder1/file2.txt"),
        }

        assert set(sorted_paths) == expected_paths
        assert sorted_paths[0] in {
            Path("folder1/subfolder1/file1.txt"),
            Path("folder1/subfolder1/file2.txt"),
        }
        assert sorted_paths[1] in {
            Path("folder1/subfolder1/file1.txt"),
            Path("folder1/subfolder1/file2.txt"),
        }
        assert sorted_paths[2] == Path("folder1/subfolder1")
        assert sorted_paths[3] == Path("folder1")

    def test_topological_sort_files_only(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=False)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        sorted_nodes = file_tree_dag.topological_sort(files_only=True)

        assert len(sorted_nodes) == 3

        sorted_paths = [node.root_rel_path for node in sorted_nodes]

        # Check that all expected files are present
        # TODO this test could be better if the topological order was deterministic
        expected_paths = {
            Path("folder1/file0.txt"),
            Path("folder1/subfolder1/file1.txt"),
            Path("folder1/subfolder1/file2.txt"),
        }
        assert set(sorted_paths) == expected_paths

    def test_topological_sort_folders_only(
        self, setup_file_tree: tuple[Path, Path, Path, Path, Path, Path]
    ) -> None:
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=False)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        sorted_nodes = file_tree_dag.topological_sort(folders_only=True)

        # Verify that only folder nodes are present and they are in correct topological order
        assert len(sorted_nodes) == 3

        # Ensure that the folders are in the correct order
        assert sorted_nodes[0].root_rel_path == Path("folder1/subfolder1")
        assert sorted_nodes[1].root_rel_path == Path("folder1")
        assert sorted_nodes[2].root_rel_path == Path("")

    @pytest.fixture
    def setup_diff_dags(self, temp_dir: Path) -> tuple[FileTreeDag, FileTreeDag]:
        structure_a = {
            "file1.txt": "hash1",
            "folder1/file2.txt": "hash2",
            "folder3/subdir/file1.txt": "hash_file_1",
            "folder3/file3.txt": "hash3",
            "folder1/thing": "has_thing_file",
        }
        dag_a = create_file_tree_dag(temp_dir / "dag_a", structure_a)

        structure_b = {
            "file1.txt": "hash1",
            "folder1/added_child.txt": "added_child",  # Added new child to dir
            "folder1/file2.txt": "hash_changed",  # Modified (hash changed only!)
            "folder2/file3.txt": "hash3",  # Added child and parent dir
            "folder3/file3.txt": "hash3",
            "folder1/thing/new_file.txt": "hash_thing_file",  # thing changes from file to folder! File is added to it so it doesn't get removed for being empty
        }
        dag_b = create_file_tree_dag(temp_dir / "dag_b", structure_b)

        # print("DAG A")
        # run_tree_command(temp_dir / "dag_a")
        # print("DAG B")
        # run_tree_command(temp_dir / "dag_b")
        return dag_a, dag_b

    def test_compute_diff_additions(
        self, setup_diff_dags: tuple[FileTreeDag, FileTreeDag]
    ) -> None:
        dag_a, dag_b = setup_diff_dags
        diff = dag_b.compute_diff(dag_a)

        added_file_node = [
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("folder2/file3.txt")
            and node.status == NodeStatus.ADDED
        ]
        assert len(added_file_node) == 1

        added_folder_node = [
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("folder2") and node.status == NodeStatus.ADDED
        ]
        assert len(added_folder_node) == 1

        added_file_node = [
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("folder1/added_child.txt")
            and node.status == NodeStatus.ADDED
        ]
        assert len(added_file_node) == 1

        modified_folder_node = [
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("folder1")
            and node.status == NodeStatus.MODIFIED
        ]
        assert len(modified_folder_node) == 1

    def test_compute_diff_modifications(
        self, setup_diff_dags: tuple[FileTreeDag, FileTreeDag]
    ) -> None:
        dag_a, dag_b = setup_diff_dags
        diff = dag_b.compute_diff(dag_a)

        assert any(
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("folder1/file2.txt")
            and node.status == NodeStatus.MODIFIED
        )
        assert any(
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("folder1")
            and node.status == NodeStatus.MODIFIED
        )

        # structure_a = {
        #     "file1.txt": "hash1",
        #     "folder1/file2.txt": "hash2",
        #     "folder3/subdir/file1.txt": "hash_file_1",
        #     "folder3/file3.txt": "hash3",
        # }
        # dag_a = create_file_tree_dag(temp_dir / "dag_a", structure_a)
        #
        # structure_b = {
        #     "file1.txt": "hash1",
        #     "folder1/added_child.txt": "added_child",  # Added new child to dir
        #     "folder1/file2.txt": "hash_changed",  # Modified (hash changed only!)
        #     "folder2/file3.txt": "hash3",  # Added child and parent dir
        #     "folder3/file3.txt": "hash3",
        #     #"folder1/thing/thing_file.txt": 'hash_thing_file',  # thing changes from file to folder! File is added
        # }

    def test_compute_diff_removals(
        self, setup_diff_dags: tuple[FileTreeDag, FileTreeDag]
    ) -> None:
        dag_a, dag_b = setup_diff_dags
        diff = dag_b.compute_diff(dag_a)

        # Starting out, the node is there.
        assert any(
            node
            for node in dag_a.root.traverse_downstream()
            if node.root_rel_path == Path("folder3/subdir/file1.txt")
        )

        # In dag_b, it's removed.
        assert not any(
            node
            for node in dag_b.root.traverse_downstream()
            if node.root_rel_path == Path("folder3/subdir/file1.txt")
        )

        # Since one child remains after removal, we're modified status for folder1
        assert any(
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("folder1")
            and node.status == NodeStatus.MODIFIED
        )

        # folder3/subdir is removed since it's children are removed
        assert not any(
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("folder3/subdir")
        )

    def test_compute_diff_unmodified_nodes(
        self, setup_diff_dags: tuple[FileTreeDag, FileTreeDag]
    ) -> None:
        dag_a, dag_b = setup_diff_dags
        diff = dag_b.compute_diff(dag_a)

        assert any(
            node
            for node in diff.root.traverse_downstream()
            if node.root_rel_path == Path("file1.txt")
            and node.status == NodeStatus.UNMODIFIED
        )

    def test_compute_diff_no_changes(self, tmp_path: Path) -> None:
        structure = {
            "file1.txt": (NodeKind.FILE, "hash1"),
            "folder1/file2.txt": (NodeKind.FILE, "hash2"),
            "folder2": (NodeKind.SUB_FOLDER, None),
        }
        dag_a = create_file_tree_dag(tmp_path / "dag_a", structure)
        dag_b = create_file_tree_dag(tmp_path / "dag_b", structure)

        diff = dag_b.compute_diff(dag_a)

        for node in diff.root.traverse_downstream():
            assert node.status == NodeStatus.UNMODIFIED

    # TODO fix implementation to support this test!!!
    # def test_compute_diff_node_kind_changes(self, setup_diff_dags: Tuple[FileTreeDag, FileTreeDag]) -> None:
    #     dag_a, dag_b = setup_diff_dags
    #     diff = dag_b.compute_diff(dag_a)
    #
    #     assert any(
    #         node
    #         for node in diff.root.traverse_downstream()
    #         if node.root_rel_path == Path("folder1/thing")
    #         and node.status == NodeStatus.ADDED
    #         and node.kind == NodeKind.SUB_FOLDER
    #     )
    #
    #     assert any(
    #         node
    #         for node in diff.root.traverse_downstream()
    #         if node.root_rel_path == Path("folder1/thing/new_file.txt")
    #         and node.status == NodeStatus.ADDED
    #         and node.kind == NodeKind.FILE
    #     )
