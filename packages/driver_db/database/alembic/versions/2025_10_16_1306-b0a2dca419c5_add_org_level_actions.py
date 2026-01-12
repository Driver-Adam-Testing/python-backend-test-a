"""add_org_level_actions

Revision ID: b0a2dca419c5
Revises: 4060b23411c9
Create Date: 2025-10-16 13:06:39.514343

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b0a2dca419c5"
down_revision = "4060b23411c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add org-level action keys
    op.execute("""
        INSERT INTO action (key, description) VALUES
        ('users.manage', 'Manage organization users and roles'),
        ('invitations.manage', 'Manage organization invitations'),
        ('subscription.read', 'View organization subscription details'),
        ('vcs.manage', 'Manage VCS integrations')
    """)

    # Grant all org-level actions to super_admin (using static UUIDs)
    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('22e14055-b3ee-47c2-8817-58baec3e79a7', 'super_admin', 'users.manage'),
        ('81de5c6e-4276-4c3e-9fac-ccfb072eaeee', 'super_admin', 'invitations.manage'),
        ('27fead60-3617-4c49-95b2-14b1734f73e0', 'super_admin', 'subscription.read'),
        ('5a890a6e-9d1e-4c32-917d-9649a02e4364', 'super_admin', 'vcs.manage')
    """)

    # Grant subscription.read to member role (using static UUID)
    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('63bf6d0e-efc8-43b7-9201-b8b1698acbf8', 'member', 'subscription.read')
    """)


def downgrade() -> None:
    # Remove role mappings
    op.execute("""
        DELETE FROM role_action_allow_org
        WHERE action_key IN ('users.manage', 'invitations.manage', 'subscription.read', 'vcs.manage')
    """)

    # Remove actions
    op.execute("""
        DELETE FROM action
        WHERE key IN ('users.manage', 'invitations.manage', 'subscription.read', 'vcs.manage')
    """)
