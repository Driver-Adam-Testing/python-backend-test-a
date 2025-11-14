"""add_org_settings_view_action

Revision ID: d2f0d4ff24d5
Revises: 21d3f60f521a
Create Date: 2025-11-14 09:31:31.729175

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d2f0d4ff24d5"
down_revision = "21d3f60f521a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add org settings actions
    op.execute("""
        INSERT INTO action (key, description) VALUES
        ('org_settings.view', 'View organization settings'),
        ('org_settings.manage', 'Manage organization settings')
    """)

    # Grant org_settings.view to org_member and org_super_admin roles
    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('3295f805-7640-4f3c-a284-5476947c42af', 'org_member', 'org_settings.view'),
        ('482a800f-2ba3-47e0-bc7c-48f384dba038', 'org_super_admin', 'org_settings.view')
    """)

    # Grant org_settings.manage to org_super_admin only
    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('bb5291ef-806c-4cb4-a798-5c26082ccbe3', 'org_super_admin', 'org_settings.manage')
    """)


def downgrade() -> None:
    # Remove role mappings
    op.execute("""
        DELETE FROM role_action_allow_org
        WHERE action_key IN ('org_settings.view', 'org_settings.manage')
    """)

    # Remove actions
    op.execute("""
        DELETE FROM action
        WHERE key IN ('org_settings.view', 'org_settings.manage')
    """)
