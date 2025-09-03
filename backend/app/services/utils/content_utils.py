import json

from database.models import DerivedContent


def _get_name_from_content_json(content: str) -> str | None:
    try:
        return json.loads(content).get("name")
    except (json.JSONDecodeError, TypeError):
        return None


def get_content_name(content: DerivedContent) -> str:
    if (
        content.content_name
    ):  # When the content name field is set in the database, we use it directly
        return content.content_name
    # For application notes, we read in the json content (saved by the frontend) and extract the name from the note content json
    # this is only needed to be backwards compatible with the old application notes
    if content.content_type.type_name == "application_note":
        name = _get_name_from_content_json(content.content)
        if name:
            return name
        if content.content:  # if name is None, we return "Generating content..." because the content is not yet ready. This is a temporary state and also only needed for backwards compatibility
            return "Generating content..."
    # Previously, when documents were uploaded, we prefixed their path with `documents/`. We no longer do that.
    # but for backwards compatibility we attempt to remove the prefix.
    if content.content_type.type_name == "supplemental-document":
        return content.relative_path.removeprefix("documents/")

    return content.relative_path
