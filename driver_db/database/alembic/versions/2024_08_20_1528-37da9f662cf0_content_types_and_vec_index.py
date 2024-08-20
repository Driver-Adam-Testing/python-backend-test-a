"""content types and vec index

Revision ID: 37da9f662cf0
Revises: 4c4d18f5c22a
Create Date: 2024-08-20 15:28:49.101478

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "37da9f662cf0"
down_revision = "4c4d18f5c22a"
branch_labels = None
depends_on = None

content_types = [
    "pdf-visual-summary",
    "pdf-text-summary",
    "pdf-image-summary",
    "pdf-extracted-text",
    "pdf-extracted-table",
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

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunkandembedding_text_embedding_3_small_vector_l2_ops ON chunkandembedding USING ivfflat (text_embedding_3_small vector_l2_ops) WITH (lists = 50);"
    )


def downgrade() -> None:
    values_clause = ", ".join(f"'{type_name}'" for type_name in content_types)
    delete_query = (
        f"DELETE FROM derived_content_types WHERE type_name IN ({values_clause});"
    )
    conn = op.get_bind()
    conn.execute(sa.text(delete_query))

    op.drop_index(
        op.f("ix_chunkandembedding_text_embedding_3_small_vector_l2_ops"),
        table_name="chunkandembedding",
    )
