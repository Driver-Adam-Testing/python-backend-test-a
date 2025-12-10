"""Add users.view

Revision ID: cf24527010fc
Revises: f84810942a3b
Create Date: 2025-10-24 13:15:37.651015

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'cf24527010fc'
down_revision = 'f84810942a3b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO action (key, description) VALUES
        ('users.view', 'View members of the organization.')
    """)

    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('8ab9c86c-0c13-4a08-80a3-02fd7fcabf1c', 'member', 'users.view')
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM action
        WHERE key IN ('users.view')
    """)

    op.execute("""
        DELETE FROM role_action_allow_org
        WHERE action_key IN ('users.view')
    """)
