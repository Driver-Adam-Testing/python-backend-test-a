"""add_autodocs_generate_action

Revision ID: d43723a6dc3c
Revises: af9eadd3bb60
Create Date: 2025-12-12 10:10:36.090742

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d43723a6dc3c"
down_revision = "af9eadd3bb60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO action (key, description) VALUES
        ('autodocs.generate', 'Generate autodocs for a page')
    """)

    # Grant autodocs.generate to asset_member role (for page assets)
    op.execute("""
        INSERT INTO role_action_allow_asset (id, role, action_key) VALUES
        ('9c7fe3ec-0822-47cb-915a-55e9a24afedb', 'asset_member', 'autodocs.generate')
    """)

    # Grant autodocs.generate to asset_admin role (for page assets)
    op.execute("""
        INSERT INTO role_action_allow_asset (id, role, action_key) VALUES
        ('28373aac-0eee-4687-8154-94178c4b9599', 'asset_admin', 'autodocs.generate')
    """)


def downgrade() -> None:
    # Remove role mappings
    op.execute("""
        DELETE FROM role_action_allow_asset
        WHERE action_key = 'autodocs.generate'
    """)

    # Remove action
    op.execute("""
        DELETE FROM action
        WHERE key = 'autodocs.generate'
    """)
