import pytest
from sqlmodel import Session
from unittest.mock import MagicMock
from app.services.content_service import ContentService
from app.schemas.content_schema import CreateContentResponse


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


@pytest.fixture
def content_service(mock_session):
    return ContentService(session=mock_session)


def test_create_blank_document(content_service):
    content_service.content_repository.create_blank_document = MagicMock(return_value=MagicMock(id="doc123"))
    response = content_service.create_blank_document("org1", "ws1", "cb1")
    assert response == CreateContentResponse(content_id="doc123")


def test_create_template(content_service):
    content_service.content_repository.create_template = MagicMock(return_value=MagicMock(id="template123"))
    response = content_service.create_template("org1", "ws1", "cb1")
    assert response == CreateContentResponse(content_id="template123")


def test_create_document_from_template(content_service):
    content_service.content_repository.create_document_from_template = MagicMock(
        return_value=MagicMock(id="docFromTemplate123"))
    response = content_service.create_document_from_template("template123")
    assert response == CreateContentResponse(content_id="docFromTemplate123")
