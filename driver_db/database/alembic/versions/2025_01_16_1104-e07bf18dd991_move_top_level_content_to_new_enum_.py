"""Move top level content to new enum values

Revision ID: e07bf18dd991
Revises: 18c0caf4bc99
Create Date: 2025-01-16 11:04:09.731137

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e07bf18dd991"
down_revision = "18c0caf4bc99"
branch_labels = None
depends_on = None
from database.nodes_v2_sql.migrate_top_level_content import MIGRATE_TOP_LEVEL


def upgrade():
    op.execute(MIGRATE_TOP_LEVEL)


def downgrade():
    pass
