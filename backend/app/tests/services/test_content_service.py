import json
import uuid
from uuid import UUID

import pytest
from sqlmodel import Session
from unittest.mock import MagicMock
from app.services.content_service import ContentService
from app.schemas.content_schema import CreateContentResponse, ListContentInput, ListContentTypesInput
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


def test_create_document_from_template(content_service, db):
    organization_id = "org_s76pU1v8LAYhTOWB"
    content_id = "content_id"
    
    new_content = content_service.create_document_from_template(organization_id, content_id)
    
    assert new_content is not None, "new_content is None"
    assert new_content.content_type.type_name == "application_note"
    assert new_content.status == Enum_Derived_Content_Status.generation_complete

    content_service.delete(new_content.id)


def test_get_list_content(content_service, db):
    organization_id = "org_s76pU1v8LAYhTOWB"
    search_input = ListContentInput(offset=0, limit=10)
    
    results = content_service.get_list_content(organization_id, search_input)
    
    assert results is not None, "results is None"
    assert len(results.results) > 0, "No content found"


def test_get_list_content_types(content_service, db):
    lct_inputs = ListContentTypesInput(offset=0, limit=10)
    
    results = content_service.get_list_content_types(lct_inputs)
    
    assert results is not None, "results is None"
    assert len(results.results) > 0, "No content types found"


def test_get_content_sources(content_service, db):
    content_id = "content_id"
    
    sources = content_service.get_content_sources(content_id)
    
    assert sources is not None, "sources is None"
    assert len(sources.results) > 0, "No sources found"


def test_create_template(content_service, db):
    organization_id = "org_s76pU1v8LAYhTOWB"
    workspace_id = UUID("90c28b84-39f9-4bd8-b7cc-6a97ef530468")
    codebase_id = UUID("cd7bf15b-ebdd-4882-96a0-df766a62227f")
    
    new_template = content_service.create_template(organization_id, workspace_id, codebase_id)
    
    assert new_template is not None, "new_template is None"
    assert new_template.content_type.type_name == "template"
    assert new_template.status == Enum_Derived_Content_Status.generation_complete

    content_service.delete(new_template.id)