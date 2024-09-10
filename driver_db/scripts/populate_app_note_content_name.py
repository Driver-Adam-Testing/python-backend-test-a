import json

from database.db import engine
from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import DerivedContent, DerivedContentType
from sqlalchemy import select
from sqlalchemy.orm import Session

MAX_INDEX_LENGTH = 2704  # Maximum length for the index


def truncate_content_name(content_name: str) -> str:
    """Truncate content_name to fit within the index size limit."""
    if len(content_name) > MAX_INDEX_LENGTH:
        return content_name[:MAX_INDEX_LENGTH]
    return content_name


def populate_content_name() -> None:
    with Session(engine) as session:
        try:
            # Query to get all derived_content of type application_note
            stmt = (
                select(DerivedContent)
                .join(DerivedContentType)
                .where(
                    DerivedContentType.type_name
                    == DerivedContentTypeNames.APPLICATION_NOTE.value
                )
            )

            results = session.execute(stmt).all()

            for row in results:
                try:
                    content = row[0]
                    # Parse the JSON content
                    content_data = json.loads(content.content)
                    # Assuming content_name is a field in the JSON content
                    content_name = content_data.get("name")
                    if content_name:
                        # Truncate the content_name if necessary
                        truncated_content_name = truncate_content_name(content_name)
                        # Update the content_name field
                        content.content_name = truncated_content_name
                except json.JSONDecodeError:
                    print(f"Failed to decode JSON for content ID: {content.id}")

            # Commit the changes
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    populate_content_name()
