"""add_usage_view_balance_action

Revision ID: 21d3f60f521a
Revises: f6f317176fcd
Create Date: 2025-11-14 09:24:41.532317

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "21d3f60f521a"
down_revision = "f6f317176fcd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the usage.view_balance action
    op.execute("""
        INSERT INTO action (key, description) VALUES
        ('usage.view_balance', 'View organization usage balance')
    """)

    # Grant usage.view_balance to org_member and org_super_admin roles
    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('c56f7c67-ed2a-43b1-b489-4aefe4b52a66', 'org_member', 'usage.view_balance'),
        ('89f14a5a-a0e3-4c38-a035-2802681517ed', 'org_super_admin', 'usage.view_balance')
    """)


def downgrade() -> None:
    # Remove role mappings
    op.execute("""
        DELETE FROM role_action_allow_org
        WHERE action_key = 'usage.view_balance'
    """)

    # Remove action
    op.execute("""
        DELETE FROM action
        WHERE key = 'usage.view_balance'
    """)
