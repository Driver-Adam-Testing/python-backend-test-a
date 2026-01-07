"""remove_cascade_delete_from_node

Revision ID: e2c37920d33c
Revises: c9147e923b0c
Create Date: 2026-01-05 16:45:29.247645

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e2c37920d33c"
down_revision = "c9147e923b0c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("node", "primary_asset_id", existing_type=sa.UUID(), nullable=True)
    op.drop_constraint("node_primary_asset_id_fkey", "node", type_="foreignkey")
    op.create_foreign_key(
        None, "node", "primary_asset", ["primary_asset_id"], ["id"], ondelete="SET NULL"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_constraint(None, "node", type_="foreignkey")
    op.create_foreign_key(
        "node_primary_asset_id_fkey",
        "node",
        "primary_asset",
        ["primary_asset_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("node", "primary_asset_id", existing_type=sa.UUID(), nullable=False)
    # ### end Alembic commands ###
