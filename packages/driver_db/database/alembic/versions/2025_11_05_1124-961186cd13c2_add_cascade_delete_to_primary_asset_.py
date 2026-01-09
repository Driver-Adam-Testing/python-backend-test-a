"""add cascade delete to primary asset role grant

Revision ID: 961186cd13c2
Revises: 0phvbxmwnk8h
Create Date: 2025-11-05 11:24:23.000484

"""

from alembic import op

revision = "961186cd13c2"
down_revision = "0phvbxmwnk8h"


def upgrade() -> None:
    op.drop_constraint(
        "primary_asset_role_grant_primary_asset_id_fkey",
        "primary_asset_role_grant",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None,
        "primary_asset_role_grant",
        "primary_asset",
        ["primary_asset_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(None, "primary_asset_role_grant", type_="foreignkey")
    op.create_foreign_key(
        "primary_asset_role_grant_primary_asset_id_fkey",
        "primary_asset_role_grant",
        "primary_asset",
        ["primary_asset_id"],
        ["id"],
    )
