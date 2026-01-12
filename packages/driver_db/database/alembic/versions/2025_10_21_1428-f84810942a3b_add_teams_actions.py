"""Add teams actions
Revision ID: f84810942a3b
Revises: 1e3476623596
Create Date: 2025-10-21 14:28:05.604719
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f84810942a3b"
down_revision = "1e3476623596"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO action (key, description) VALUES
        ('team.view', 'View members of the team.'),
        ('team.manage', 'May add and remove members of the team.'),
        ('team.admin', 'May create and delete teams.')
    """)

    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('66f75fa6-b73f-443f-8fec-5d687ab925a7', 'super_admin', 'team.view'),
        ('43120baa-109a-4999-83d0-67f79334bf72', 'super_admin', 'team.manage'),
        ('fd965c81-3c3f-4215-aed9-46d5d3fd1c5a', 'super_admin', 'team.admin'),
        ('1d5727d7-8cda-4b85-a7c4-8a181eecd7e5', 'member', 'team.view')
    """)

    op.execute("""
        INSERT INTO role_action_allow_team (id, role, action_key) VALUES
        ('a84377b2-e8d0-4b26-9019-51290272af0f', 'member', 'team.view'),
        ('8c93f1e1-c84f-47ce-9bfb-4c828e205104', 'team_admin', 'team.manage'),
        ('12f49083-c761-4841-884d-0b53ec4aa8a6', 'team_admin', 'team.view')
    """)


def downgrade() -> None:
    # Remove role mappings
    op.execute("""
        DELETE FROM role_action_allow_org
        WHERE action_key IN ('team.view', 'team.manage', 'team.admin')
    """)

    op.execute("""
        DELETE FROM role_action_allow_team
        WHERE action_key IN ('team.view', 'team.manage', 'team.admin')
    """)

    op.execute("""
        DELETE FROM action
        WHERE key IN ('team.view', 'team.manage', 'team.admin')
    """)
