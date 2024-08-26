from uuid import uuid4

import pytest
from database.models_v1 import DerivedContent, DerivedContentType, Workspace

from app.api.content.content_resolution import (
    build_resolve_content_query,
    build_resolve_paths_query,
    find_minimal_inclusion_paths,
)


@pytest.fixture
def workspace(db):
    workspace = Workspace(id=uuid4(), organization_id=str(uuid4()))
    db.add(workspace)
    db.commit()
    return workspace


@pytest.fixture
def content_type(db):
    content_type = DerivedContentType(id=uuid4(), type_name="TEST_TYPE")
    db.add(content_type)
    db.commit()
    return content_type


class TestBuildResolvePathsQuery:
    def test_include_single_path(self, db, workspace, content_type):
        derived_content = DerivedContent(
            id=uuid4(),
            workspace_id=workspace.id,
            content_type_id=content_type.id,
            relative_path="my/path",
        )
        db.add(derived_content)
        db.commit()

        include_ids = [derived_content.id]

        query = build_resolve_paths_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 1
        assert results[0] == "my/path"

    def test_include_single_path_with_trailing_slash(self, db, workspace, content_type):
        derived_content = DerivedContent(
            id=uuid4(),
            workspace_id=workspace.id,
            content_type_id=content_type.id,
            relative_path="my/path/",
        )
        db.add(derived_content)
        db.commit()

        include_ids = [derived_content.id]

        query = build_resolve_paths_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 1
        assert results[0] == "my/path"  # Trailing slash should be removed

    def test_include_multiple_paths(self, db, workspace, content_type):
        derived_contents = [
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/deeper",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/other",
            ),
        ]
        db.add_all(derived_contents)
        db.commit()

        include_ids = [content.id for content in derived_contents]

        query = build_resolve_paths_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        expected_paths = {"my/path", "my/path/deeper", "my/path/other"}
        assert set(results) == expected_paths

    def test_deduplicate_paths(self, db, workspace, content_type):
        derived_contents = [
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path",
            ),
        ]
        db.add_all(derived_contents)
        db.commit()

        include_ids = [content.id for content in derived_contents]

        query = build_resolve_paths_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 1
        assert results[0] == "my/path"  # Deduplicated

    def test_deduplicate_paths_with_trailing_slash(self, db, workspace, content_type):
        derived_contents = [
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path",
            ),
        ]
        db.add_all(derived_contents)
        db.commit()

        include_ids = [content.id for content in derived_contents]

        query = build_resolve_paths_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 1
        assert results[0] == "my/path"  # Deduplicated and normalized


class TestFindMinimalInclusionPaths:
    def test_single_path(self):
        paths = ["my/path"]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"my/path"}

    def test_multiple_unrelated_paths(self):
        paths = ["my/path", "other/path", "another/path"]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"my/path", "other/path", "another/path"}

    def test_parent_and_child_paths(self):
        paths = ["my/path", "my/path/deeper", "my/path/other"]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"my/path"}

    def test_sibling_paths(self):
        paths = ["my/path/deeper", "my/path/other"]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"my/path/deeper", "my/path/other"}

    def test_nested_hierarchy(self):
        paths = [
            "my/path",
            "my/path/deeper/level1",
            "my/path/deeper",
            "my/path/deeper/level1/level2",
        ]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"my/path"}

    def test_root_path_included(self):
        paths = ["/", "/my/path", "/other/path"]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"/"}

    def test_mixed_hierarchy(self):
        paths = ["my/path", "my/path/deeper", "my/other", "another/path", "my"]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"my", "another/path"}

    def test_trailing_slash_paths(self):
        paths = ["my/path/", "my/path/deeper/", "my/path/other/"]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"my/path"}

    def test_empty_list(self):
        paths = []
        result = find_minimal_inclusion_paths(paths)
        assert result == set()

    def test_single_root_path(self):
        paths = ["/"]
        result = find_minimal_inclusion_paths(paths)
        assert result == {"/"}


class TestBuildResolveContentQuery:
    def test_include_single_path(self, db, workspace, content_type):
        derived_content = DerivedContent(
            id=uuid4(),
            workspace_id=workspace.id,
            content_type_id=content_type.id,
            relative_path="my/path",
        )
        db.add(derived_content)
        db.commit()

        include_ids = [derived_content.id]

        query = build_resolve_content_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 1
        assert any(content.relative_path == "my/path" for content in results)

    def test_include_single_path_with_trailing_slash(self, db, workspace, content_type):
        derived_content = DerivedContent(
            id=uuid4(),
            workspace_id=workspace.id,
            content_type_id=content_type.id,
            relative_path="my/path/",
        )
        db.add(derived_content)
        db.commit()

        include_ids = [derived_content.id]

        query = build_resolve_content_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 1
        assert any(content.relative_path == "my/path/" for content in results)

    def test_include_path_with_subpaths(self, db, workspace, content_type):
        derived_contents = [
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/deeper",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/other",
            ),
        ]
        db.add_all(derived_contents)
        db.commit()

        include_ids = [derived_contents[0].id]

        query = build_resolve_content_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 3
        assert all(content.relative_path.startswith("my/path") for content in results)

    def test_include_path_with_trailing_slash_and_subpaths(
        self, db, workspace, content_type
    ):
        derived_contents = [
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/deeper",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/other",
            ),
        ]
        db.add_all(derived_contents)
        db.commit()

        include_ids = [derived_contents[0].id]

        query = build_resolve_content_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 3
        assert all(content.relative_path.startswith("my/path") for content in results)

    def test_include_path_with_and_without_trailing_slash(
        self, db, workspace, content_type
    ):
        derived_contents = [
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/",
            ),
            DerivedContent(
                id=uuid4(),
                workspace_id=workspace.id,
                content_type_id=content_type.id,
                relative_path="my/path/deeper",
            ),
        ]
        db.add_all(derived_contents)
        db.commit()

        include_ids = [
            derived_contents[1].id
        ]  # Include the one with the trailing slash

        query = build_resolve_content_query(workspace.organization_id, include_ids)
        results = db.exec(query).all()

        assert len(results) == 3
        assert any(content.relative_path == "my/path" for content in results)
        assert any(content.relative_path == "my/path/" for content in results)
        assert any(content.relative_path == "my/path/deeper" for content in results)
