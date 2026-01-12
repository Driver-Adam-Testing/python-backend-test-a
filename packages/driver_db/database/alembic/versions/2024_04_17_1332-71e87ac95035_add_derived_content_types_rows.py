"""Add derived_content_types rows

Revision ID: 71e87ac95035
Revises: 3819ef9c4dec
Create Date: 2024-04-17 13:32:32.795762

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "71e87ac95035"
down_revision: str | None = "3819ef9c4dec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

content_types = [
    "short_paragraph_description",
    "terse_sentence_description",
    "long_description",
    "quick_start_entry",
    "quick_start_getting_started",
    "quick_start_dependencies",
    "quick_start_use",
    "architecture_diagram",
    "chunk_descriptions",
    "application_note",
    "short_sentence_description",
    "derived_content_types",
]


def upgrade() -> None:
    existing_types_query = "SELECT type_name FROM derived_content_types;"
    conn = op.get_bind()
    existing_types_result = conn.execute(sa.text(existing_types_query))
    existing_types = {row["type_name"] for row in existing_types_result}

    # Build the SQL insert statement only for new types not existing
    new_types = [
        type_name for type_name in content_types if type_name not in existing_types
    ]
    if new_types:
        values_clause = ", ".join(f"('{type_name}')" for type_name in new_types)
        insert_query = (
            f"INSERT INTO derived_content_types (type_name) VALUES {values_clause};"
        )
        conn.execute(sa.text(insert_query))


def downgrade() -> None:
    values_clause = ", ".join(f"'{type_name}'" for type_name in content_types)
    delete_query = (
        f"DELETE FROM derived_content_types WHERE type_name IN ({values_clause});"
    )
    conn = op.get_bind()
    conn.execute(sa.text(delete_query))
