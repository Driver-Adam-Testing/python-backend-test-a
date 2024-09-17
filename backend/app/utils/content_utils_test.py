import unittest
from unittest.mock import Mock
from backend.app.utils.content_utils import get_name_from_content_json, get_content_name
from database.models_v1 import DerivedContent


class TestContentUtils(unittest.TestCase):
    def test_get_name_from_content_json_valid(self):
        content = '{"name": "Test Name"}'
        self.assertEqual(get_name_from_content_json(content), "Test Name")

    def test_get_name_from_content_json_invalid_json(self):
        content = '{"name": "Test Name"'
        self.assertIsNone(get_name_from_content_json(content))

    def test_get_name_from_content_json_no_name(self):
        content = '{"title": "Test Title"}'
        self.assertIsNone(get_name_from_content_json(content))

    def test_get_name_from_content_json_none(self):
        content = None
        self.assertIsNone(get_name_from_content_json(content))

    def test_get_content_name_with_content_name(self):
        content = Mock(spec=DerivedContent)
        content.content_name = "Existing Name"
        self.assertEqual(get_content_name(content), "Existing Name")

    def test_get_content_name_application_note_with_name(self):
        content = Mock(spec=DerivedContent)
        content.content_name = None
        content.content_type.type_name = "application_note"
        content.content = '{"name": "App Note Name"}'
        self.assertEqual(get_content_name(content), "App Note Name")

    def test_get_content_name_application_note_generating(self):
        content = Mock(spec=DerivedContent)
        content.content_name = None
        content.content_type.type_name = "application_note"
        content.content = '{"title": "App Note Title"}'
        self.assertEqual(get_content_name(content), "Generating content...")

    def test_get_content_name_supplemental_document(self):
        content = Mock(spec=DerivedContent)
        content.content_name = None
        content.content_type.type_name = "supplemental-document"
        content.relative_path = "documents/supplemental.pdf"
        self.assertEqual(get_content_name(content), "supplemental.pdf")

    def test_get_content_name_default(self):
        content = Mock(spec=DerivedContent)
        content.content_name = None
        content.content_type.type_name = "other"
        content.relative_path = "other/path/to/content"
        self.assertEqual(get_content_name(content), "other/path/to/content")


if __name__ == "__main__":
    unittest.main()
