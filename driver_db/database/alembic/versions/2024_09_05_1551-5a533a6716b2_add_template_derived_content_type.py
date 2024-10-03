"""Add template derived_content_type

Revision ID: 5a533a6716b2
Revises: df374eaa585a
Create Date: 2024-09-05 15:51:19.379920

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5a533a6716b2"
down_revision = "df374eaa585a"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insert_query = "INSERT INTO derived_content_types (type_name) VALUES ('template');"
    conn.execute(sa.text(insert_query))


def downgrade():
    conn = op.get_bind()
    delete_query = "DELETE FROM derived_content_types WHERE type_name = 'template';"
    conn.execute(sa.text(delete_query))
