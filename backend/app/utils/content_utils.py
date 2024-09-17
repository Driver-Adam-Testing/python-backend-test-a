from database.models_v1 import DerivedContent
import json


def get_name_from_content_json(content: str) -> str | None:
    """
    Extracts the 'name' field from a JSON string.

    Args:
        content (str): A JSON string containing the content.

    Returns:
        str | None: The value of the 'name' field if present, otherwise None.
    """
    try:
        return json.loads(content).get("name")
    except (json.JSONDecodeError, TypeError):
        return None


def get_content_name(content: DerivedContent) -> str:
    """
    Determines the name of the content based on its type and attributes.

    Args:
        content (DerivedContent): An instance of DerivedContent.

    Returns:
        str: The name of the content.
    """
    if content.content_name:
        return content.content_name

    if content.content_type.type_name == "application_note":
        name = get_name_from_content_json(content.content)
        if name:
            return name
        if content.content:
            return "Generating content..."

    if content.content_type.type_name == "supplemental-document":
        return content.relative_path.removeprefix("documents/")

    return content.relative_path
