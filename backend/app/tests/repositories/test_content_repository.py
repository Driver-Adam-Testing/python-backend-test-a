import json

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import NoResultFound
from datetime import datetime
from app.repositories.content_repository import ContentRepository
from database.models_v1 import (
    DerivedContent,
    DerivedContentType,
    Workspace,
    Enum_Derived_Content_Status
)


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def content_repository(session):
    return ContentRepository(session)


def test_create_blank_document(content_repository, session):
    # Mock the workspace_repository.exists method to return True
    content_repository.workspace_repository = MagicMock()
    content_repository.workspace_repository.exists.return_value = True

    # Mock the derived_content_type_repository.get_by_type_name method
    content_repository.derived_content_type_repository = MagicMock()
    content_repository.derived_content_type_repository.get_by_type_name.side_effect = [
        MagicMock(id="application_note_content_type_id"),  # Application note content type
        MagicMock(id="codebase_content_type_id")  # Codebase content type
    ]

    session.exec.return_value.first.side_effect = [
        MagicMock(id="parent_content_id", relative_path="path/to/parent")  # Parent content
    ]

    new_content = content_repository.create_blank_document("org_id", "workspace_id", "codebase_id")

    # Debugging assertions
    assert new_content is not None, "new_content is None"
    assert hasattr(new_content, 'content_type_id'), "new_content does not have attribute 'content_type_id'"
    assert new_content.content_type_id == "application_note_content_type_id", f"Expected 'application_note_content_type_id', got {new_content.content_type_id}"
    assert new_content.workspace_id == "workspace_id"
    assert new_content.source_content_id == "parent_content_id", f"Expected 'parent_content_id', got {new_content.source_content_id}"
    assert new_content.codebase_id == "codebase_id"
    assert new_content.relative_path == "path/to/parent"
    assert new_content.status == Enum_Derived_Content_Status.generation_complete


def test_create_blank_document_workspace_not_found(content_repository, session):
    session.exec.return_value.first.side_effect = NoResultFound

    with pytest.raises(NoResultFound):
        content_repository.create_blank_document("org_id", "workspace_id", "codebase_id")


def test_create_template(content_repository, session):
    # Mock the workspace_repository.exists method to return True
    content_repository.workspace_repository = MagicMock()
    content_repository.workspace_repository.exists.return_value = True

    # Mock the derived_content_type_repository.get_by_type_name method
    content_repository.derived_content_type_repository = MagicMock()
    content_repository.derived_content_type_repository.get_by_type_name.side_effect = [
        MagicMock(id="template_content_type_id"),  # Template content type
        MagicMock(id="codebase_content_type_id")  # Codebase content type
    ]

    session.exec.return_value.first.side_effect = [
        MagicMock(id="parent_content_id", relative_path="path/to/parent")  # Parent content
    ]

    new_content = content_repository.create_template("org_id", "workspace_id", "codebase_id")

    assert new_content.content_type_id == "template_content_type_id"
    assert new_content.workspace_id == "workspace_id"
    assert new_content.source_content_id == "parent_content_id"
    assert new_content.codebase_id == "codebase_id"
    assert new_content.relative_path == "path/to/parent"
    assert new_content.status == Enum_Derived_Content_Status.generation_complete


def test_create_template_workspace_not_found(content_repository, session):
    session.exec.return_value.first.side_effect = NoResultFound

    with pytest.raises(NoResultFound):
        content_repository.create_template("org_id", "workspace_id", "codebase_id")


def test_create_document_from_template(content_repository, session):
    # Mock the derived_content_type_repository.get_by_type_name method
    content_repository.derived_content_type_repository = MagicMock()
    content_repository.derived_content_type_repository.get_by_type_name.side_effect = [
        MagicMock(id="template_content_type_id"),  # Template content type
        MagicMock(id="application_note_content_type_id")  # Application note content type
    ]

    session.exec.return_value.first.side_effect = [
        MagicMock(
            id="content_id",
            content=json.dumps({"name": "Template"}),
            content_type_id="template_content_type_id",
            workspace_id="workspace_id",
            source_content_id="source_content_id",
            codebase_id="codebase_id",
            relative_path="path/to/parent"
        )  # Content
    ]

    new_content = content_repository.create_document_from_template("content_id")

    assert new_content.content_type_id == "application_note_content_type_id"
    assert new_content.workspace_id == "workspace_id"
    assert new_content.source_content_id == "source_content_id"
    assert new_content.codebase_id == "codebase_id"
    assert new_content.relative_path == "path/to/parent"
    assert new_content.status == Enum_Derived_Content_Status.generation_complete
    assert json.loads(new_content.content)["name"] == "Template (Copy)"


def test_create_document_from_template_content_not_found(content_repository, session):
    session.exec.return_value.first.side_effect = NoResultFound

    with pytest.raises(NoResultFound):
        content_repository.create_document_from_template("content_id")