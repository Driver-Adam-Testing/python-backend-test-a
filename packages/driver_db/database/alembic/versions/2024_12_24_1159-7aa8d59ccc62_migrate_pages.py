"""migrate pages

Revision ID: 7aa8d59ccc62
Revises: 20b952b9cbe7
Create Date: 2024-12-24 11:59:55.607659

"""

from alembic import op

from database.nodes_v2_sql.migrate_pages_and_templates import MIGRATE_PAGES

# revision identifiers, used by Alembic.
revision = "7aa8d59ccc62"
down_revision = "20b952b9cbe7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(MIGRATE_PAGES)


def downgrade():
    pass
