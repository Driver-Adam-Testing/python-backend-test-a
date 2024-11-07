"""Add missing pdf_summary record if needed
Revision ID: 785ce738f845
Revises: 5c80dca0c06c
Create Date: 2024-10-16 11:31:18.322963
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "785ce738f845"
down_revision = "5c80dca0c06c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_types_query = (
        "SELECT type_name FROM derived_content_types where type_name = 'pdf_summary';"
    )
    conn = op.get_bind()
    existing_type_result = conn.execute(sa.text(existing_types_query))

    if len(list(existing_type_result)) == 0:
        insert_query = (
            "INSERT INTO derived_content_types (type_name) VALUES ('pdf_summary');"
        )
        conn.execute(sa.text(insert_query))


def downgrade() -> None:
    delete_query = "DELETE FROM derived_content_types WHERE type_name='pdf_summary';"
    conn = op.get_bind()
    conn.execute(sa.text(delete_query))
