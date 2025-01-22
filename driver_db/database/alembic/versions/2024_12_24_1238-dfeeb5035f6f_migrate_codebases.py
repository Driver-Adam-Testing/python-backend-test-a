"""migrate codebases

Revision ID: dfeeb5035f6f
Revises: 3465397ed16c
Create Date: 2024-12-24 12:38:17.268125

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "dfeeb5035f6f"
down_revision = "3465397ed16c"
branch_labels = None
depends_on = None
from database.nodes_v2_sql.migrate_codebases import MIGRATE_CODEBASE


def upgrade():
    op.execute(MIGRATE_CODEBASE)


def downgrade():
    pass
