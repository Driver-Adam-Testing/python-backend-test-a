"""migrate pdfs

Revision ID: 3465397ed16c
Revises: 7aa8d59ccc62
Create Date: 2024-12-24 12:19:05.020370

"""

from alembic import op
from database.nodes_v2_sql.migrate_pdfs import MIGRATE_PDFS

# revision identifiers, used by Alembic.
revision = "3465397ed16c"
down_revision = "7aa8d59ccc62"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(MIGRATE_PDFS)


def downgrade():
    pass
