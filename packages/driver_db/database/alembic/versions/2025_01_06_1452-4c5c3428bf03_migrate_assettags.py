"""migrate assettags

Revision ID: 4c5c3428bf03
Revises: 7478d83c8205
Create Date: 2025-01-06 14:52:02.628677

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "4c5c3428bf03"
down_revision = "7478d83c8205"
branch_labels = None
depends_on = None
from database.nodes_v2_sql.migrate_tags import MIGRATE_TAGS


def upgrade():
    op.execute(MIGRATE_TAGS)


def downgrade():
    pass
