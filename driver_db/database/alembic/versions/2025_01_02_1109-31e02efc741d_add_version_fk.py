"""Add version fk

Revision ID: 31e02efc741d
Revises: 746ab52e9211
Create Date: 2025-01-02 11:09:55.516988

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "31e02efc741d"
down_revision = "746ab52e9211"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("inspectorrun", sa.Column("version_id", sa.Uuid(), nullable=True))
    op.alter_column(
        "inspectorrun", "inspection_version_id", existing_type=sa.UUID(), nullable=True
    )
    op.create_foreign_key(None, "inspectorrun", "v2_version", ["version_id"], ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    pass
