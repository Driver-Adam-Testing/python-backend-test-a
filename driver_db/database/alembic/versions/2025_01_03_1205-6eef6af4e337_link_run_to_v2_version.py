"""Link run to v2 version

Revision ID: 6eef6af4e337
Revises: 31e02efc741d
Create Date: 2025-01-03 12:05:16.460100

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "6eef6af4e337"
down_revision = "31e02efc741d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE inspector_run
        SET version_id = inspection_version_id
    """)


def downgrade() -> None:
    pass
