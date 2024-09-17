"""Add missing symbol record if needed

Revision ID: 54fb48ccdd81
Revises: c3c66c4c4201
Create Date: 2024-09-17 13:10:13.704583

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "54fb48ccdd81"
down_revision = "c3c66c4c4201"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_types_query = (
        "SELECT type_name FROM derived_content_types where type_name = 'symbol';"
    )
    conn = op.get_bind()
    existing_type_result = conn.execute(sa.text(existing_types_query))

    if len(list(existing_type_result)) == 0:
        insert_query = (
            "INSERT INTO derived_content_types (type_name) VALUES ('symbol');"
        )
        conn.execute(sa.text(insert_query))


def downgrade() -> None:
    delete_query = "DELETE FROM derived_content_types WHERE type_name='symbol';"
    conn = op.get_bind()
    conn.execute(sa.text(delete_query))
