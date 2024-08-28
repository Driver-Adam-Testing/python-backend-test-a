from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from .dag import FileTreeDag, LiteNode, Node, NodeKind, NodeStatus


class TestNode:
    @pytest.fixture
    def root_node(self):
        return Node(
            kind=NodeKind.ROOT_FOLDER,
            root_rel_path=Path("/"),
            parent=None,
            status=NodeStatus.UNMODIFIED,
        )

    @pytest.fixture
    def child_node(self):
        return Node(
            kind=NodeKind.SUB_FOLDER,
            root_rel_path=Path("/child"),
            parent=None,
            status=NodeStatus.UNMODIFIED,
        )

    @pytest.fixture
    def second_child_node(self):
        return Node(
            kind=NodeKind.SUB_FOLDER,
            root_rel_path=Path("/child2"),
            parent=None,
            status=NodeStatus.UNMODIFIED,
        )

    @pytest.fixture
    def grandchild_node(self):
        return Node(
            kind=NodeKind.FILE,
            root_rel_path=Path("/child/grandchild"),
            parent=None,
            status=NodeStatus.UNMODIFIED,
        )

    def test_add_child(self, root_node, child_node, grandchild_node):
        # Add child to root
        root_node.add_child(child_node)
        assert child_node.parent == root_node
        assert root_node.children["/child"] == child_node

        # Add grandchild to child
        child_node.add_child(grandchild_node)
        assert grandchild_node.parent == child_node
        assert child_node.children["/child/grandchild"] == grandchild_node
        assert grandchild_node.root_rel_path == Path("/child/grandchild")

    def test_remove_child(self, root_node, child_node, grandchild_node):
        root_node.add_child(child_node)
        child_node.add_child(grandchild_node)

        root_node.remove_child(Path("/child"))
        assert Path("/child") not in root_node.children
        assert child_node.parent is None

    def test_traverse_upstream(self, grandchild_node, child_node, root_node):
        root_node.add_child(child_node)
        child_node.add_child(grandchild_node)

        # Traverse upstream from grandchild
        upstream_nodes = list(grandchild_node.traverse_upstream())
        assert upstream_nodes == [grandchild_node, child_node, root_node]

    def test_traverse_downstream(
        self, grandchild_node, child_node, second_child_node, root_node
    ):
        root_node.add_child(child_node)
        root_node.add_child(second_child_node)
        child_node.add_child(grandchild_node)

        # Traverse downstream from root
        downstream_nodes = list(root_node.traverse_downstream())
        assert downstream_nodes == [
            root_node,
            child_node,
            grandchild_node,
            second_child_node,
        ]

        # Traverse downstream from child
        downstream_nodes_from_child = list(child_node.traverse_downstream())
        assert downstream_nodes_from_child == [child_node, grandchild_node]

        # Traverse downstream from second child, which only gives 'self'.
        downstream_nodes_from_child = list(second_child_node.traverse_downstream())
        assert downstream_nodes_from_child == [second_child_node]

    def test_into_lite_node(self, grandchild_node):
        lite_node = grandchild_node.into_lite_node()
        assert isinstance(lite_node, LiteNode)
        assert lite_node.kind == grandchild_node.kind
        assert lite_node.root_rel_path == grandchild_node.root_rel_path


class TestFileTreeDag:
    @pytest.fixture
    def temp_dir(self):
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def setup_file_tree(self, temp_dir: Path):
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

    def test_add_file_marks_ancestors_as_added(self, setup_file_tree):
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

    def test_remove_file_marks_parents_as_modified(self, setup_file_tree):
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
        self, setup_file_tree
    ):
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
        self, setup_file_tree
    ):
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=True)
        file_tree_dag.add_file(test_file1, change_status=True)
        file_tree_dag.add_file(test_file2, change_status=True)

        # Test
        file_tree_dag.mark_file_removal(test_file1)

        # Verify that the ancestor is not marked as removed because it still has an active child
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
        )  # Still exists

    def test_mark_as_modified_propagates_to_parents(self, setup_file_tree):
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=False)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        # Test
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

    def test_mark_as_modified_propagates_to_children(self, setup_file_tree):
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

        # Verify that the folder and its children are marked as modified
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
        self, setup_file_tree
    ):
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file0, change_status=False)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        # Test
        file_tree_dag.mark_as_modified(
            test_file1, include_upstream=False, include_downstream=False
        )

        # Verify that only the file itself is marked as modified
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

    def test_topological_sort_all_nodes(self, setup_file_tree):
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        # file_tree_dag.add_file(test_file0, change_status=False)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        sorted_nodes = file_tree_dag.topological_sort()

        # Verify that all nodes are present in the correct order
        assert len(sorted_nodes) == 5  # root, folder1, subfolder1, file1.txt, file2.txt
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

    def test_topological_sort_changed_nodes_only(self, setup_file_tree):
        root_abs_path, test_file0, test_file1, test_file2, *_ = setup_file_tree
        file_tree_dag = FileTreeDag(root_abs_path=root_abs_path)
        file_tree_dag.add_file(test_file1, change_status=False)
        file_tree_dag.add_file(test_file2, change_status=False)

        file_tree_dag.mark_file_removal(test_file1)
        sorted_nodes = file_tree_dag.topological_sort(changed_nodes_only=True)

        # Verify that only the modified/removed nodes are present
        assert len(sorted_nodes) == 4
        assert sorted_nodes[0].root_rel_path == Path("folder1/subfolder1/file1.txt")
        assert sorted_nodes[1].root_rel_path == Path("folder1/subfolder1")
        assert sorted_nodes[2].root_rel_path == Path("folder1")
        assert sorted_nodes[3].root_rel_path == Path("")

    def test_topological_sort_files_only(self, setup_file_tree):
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

    def test_topological_sort_folders_only(self, setup_file_tree):
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
