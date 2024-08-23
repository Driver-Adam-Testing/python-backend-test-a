from uuid import uuid4

import pytest
from database.models_v1 import DerivedContent, DerivedContentType, Workspace

from app.api.content.content_resolution import build_resolve_content_query


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


def test_include_single_path(db, workspace, content_type):
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


def test_include_single_path_with_trailing_slash(db, workspace, content_type):
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


def test_include_path_with_subpaths(db, workspace, content_type):
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


def test_include_path_with_trailing_slash_and_subpaths(db, workspace, content_type):
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


def test_include_path_with_and_without_trailing_slash(db, workspace, content_type):
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

    include_ids = [derived_contents[1].id]  # Include the one with the trailing slash

    query = build_resolve_content_query(workspace.organization_id, include_ids)
    results = db.exec(query).all()

    assert len(results) == 3
    assert any(content.relative_path == "my/path" for content in results)
    assert any(content.relative_path == "my/path/" for content in results)
    assert any(content.relative_path == "my/path/deeper" for content in results)
