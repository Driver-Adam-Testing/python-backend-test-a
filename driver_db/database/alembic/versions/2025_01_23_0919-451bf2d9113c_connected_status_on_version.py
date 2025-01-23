"""connected status on version

Revision ID: 451bf2d9113c
Revises: 25d3fa4abdc5
Create Date: 2025-01-23 09:19:33.564478

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "451bf2d9113c"
down_revision = "25d3fa4abdc5"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE versionstatus ADD VALUE 'CONNECTED'")


def downgrade():
    pass
