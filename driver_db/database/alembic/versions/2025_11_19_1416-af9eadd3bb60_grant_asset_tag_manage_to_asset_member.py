"""grant_asset_tag_manage_to_asset_member

Revision ID: af9eadd3bb60
Revises: 9ea04975db27
Create Date: 2025-11-19 14:16:31.295411

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "af9eadd3bb60"
down_revision = "9ea04975db27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO role_action_allow_asset (id, role, action_key) VALUES
        ('052f3d51-baa6-4659-bb70-42acbdbe779d', 'asset_member', 'asset_tag.manage')
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM role_action_allow_asset
        WHERE id = '052f3d51-baa6-4659-bb70-42acbdbe779d'
    """)
