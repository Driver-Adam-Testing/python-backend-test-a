from unittest.mock import Mock

import pytest
from database.models import DerivedContent

from app.services.utils.content_utils import (
    _get_name_from_content_json,
    get_content_name,
)


def test_get_name_from_content_json_valid():
    content = '{"name": "Test Name"}'
    assert _get_name_from_content_json(content) == "Test Name"


def test_get_name_from_content_json_invalid_json():
    content = '{"name": "Test Name"'
    assert _get_name_from_content_json(content) is None


def test_get_name_from_content_json_no_name():
    content = '{"title": "Test Title"}'
    assert _get_name_from_content_json(content) is None


def test_get_name_from_content_json_none():
    content = None
    assert _get_name_from_content_json(content) is None


def test_get_content_name_with_content_name():
    content = Mock(spec=DerivedContent)
    content.content_name = "Existing Name"
    assert get_content_name(content) == "Existing Name"


def test_get_content_name_application_note_with_name():
    content = Mock(spec=DerivedContent)
    content.content_name = None
    content.content_type.type_name = "application_note"
    content.content = '{"name": "App Note Name"}'
    assert get_content_name(content) == "App Note Name"


def test_get_content_name_application_note_generating():
    content = Mock(spec=DerivedContent)
    content.content_name = None
    content.content_type.type_name = "application_note"
    content.content = '{"title": "App Note Title"}'
    assert get_content_name(content) == "Generating content..."


def test_get_content_name_supplemental_document():
    content = Mock(spec=DerivedContent)
    content.content_name = None
    content.content_type.type_name = "supplemental-document"
    content.relative_path = "documents/supplemental.pdf"
    assert get_content_name(content) == "supplemental.pdf"


def test_get_content_name_default():
    content = Mock(spec=DerivedContent)
    content.content_name = None
    content.content_type.type_name = "other"
    content.relative_path = "other/path/to/content"
    assert get_content_name(content) == "other/path/to/content"


if __name__ == "__main__":
    pytest.main()
