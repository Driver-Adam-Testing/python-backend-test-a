"""remove_org_member_team_view_permission

Revision ID: 08311608dc98
Revises: d2f0d4ff24d5
Create Date: 2025-11-14 09:54:54.616803

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "08311608dc98"
down_revision = "d2f0d4ff24d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove team.view permission from org_member at org level
    # org_members should only see teams they're members of (via team-level permission)
    # org_super_admins retain this permission to view all teams
    op.execute("""
        DELETE FROM role_action_allow_org
        WHERE role = 'member' AND action_key = 'team.view'
        AND id = '1d5727d7-8cda-4b85-a7c4-8a181eecd7e5'
    """)


def downgrade() -> None:
    # Restore team.view permission for org_member at org level
    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('1d5727d7-8cda-4b85-a7c4-8a181eecd7e5', 'member', 'team.view')
    """)
