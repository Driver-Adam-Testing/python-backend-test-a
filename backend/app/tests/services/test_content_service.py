import json
import uuid
from uuid import UUID

import pytest
from sqlmodel import Session
from unittest.mock import MagicMock
from app.services.content_service import ContentService
from app.schemas.content_schema import CreateContentResponse
from sqlalchemy.exc import NoResultFound

from database.models_v1 import Enum_Derived_Content_Status


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


@pytest.fixture
def content_service(mock_session):
    return ContentService(session=mock_session)



def test_create_blank_document(content_service, db):
    workspace_id = UUID("90c28b84-39f9-4bd8-b7cc-6a97ef530468")
    codebase_id = UUID("cd7bf15b-ebdd-4882-96a0-df766a62227f")
    org_id = "org_s76pU1v8LAYhTOWB"
    new_content = content_service.create_blank_document(org_id, workspace_id, codebase_id)

    # Debugging assertions
    assert new_content is not None, "new_content is None"
    assert hasattr(new_content, 'content_type_id'), "new_content does not have attribute 'content_type_id'"
    assert new_content.content_type.type_name == "application_note"
    assert new_content.workspace_id == workspace_id
    assert new_content.codebase_id == codebase_id
    assert new_content.status == Enum_Derived_Content_Status.generation_complete

    content_service.delete(new_content.id)


def test_create_blank_document_with_name(content_service, db):
    workspace_id = UUID("90c28b84-39f9-4bd8-b7cc-6a97ef530468")
    codebase_id = UUID("cd7bf15b-ebdd-4882-96a0-df766a62227f")
    org_id = "org_s76pU1v8LAYhTOWB"
    new_content = content_service.create_blank_document(org_id, workspace_id, codebase_id, "Test Note")

    # Debugging assertions
    assert new_content is not None, "new_content is None"
    assert hasattr(new_content, 'content_type_id'), "new_content does not have attribute 'content_type_id'"
    assert new_content.content_type.type_name == "application_note"
    assert new_content.workspace_id == workspace_id
    assert new_content.codebase_id == codebase_id
    assert new_content.status == Enum_Derived_Content_Status.generation_complete

    assert json.loads(new_content.content)["name"] == "Test Note"
    content_service.delete(new_content.id)


def test_create_blank_document_workspace_not_found(content_service, db):
    # db.exec.return_value.first.side_effect = NoResultFound
    non_existent_workspace_id = str(uuid.uuid4())

    with pytest.raises(NoResultFound):
        content_service.create_blank_document("org_id", non_existent_workspace_id, "codebase_id")