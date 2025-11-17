"""restore_org_member_team_view_permission

Revision ID: 9ea04975db27
Revises: 08311608dc98
Create Date: 2025-11-17 08:27:14.036398

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9ea04975db27"
down_revision = "08311608dc98"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Restore team.view permission for org_member at org level
    # This is needed for listing/searching teams - the listing endpoints use enforce_org_action
    # Team-level permissions still control which specific teams a user can view details for
    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('1d5727d7-8cda-4b85-a7c4-8a181eecd7e5', 'org_member', 'team.view')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    # Remove team.view permission from org_member at org level
    op.execute("""
        DELETE FROM role_action_allow_org
        WHERE role = 'org_member' AND action_key = 'team.view'
        AND id = '1d5727d7-8cda-4b85-a7c4-8a181eecd7e5'
    """)
