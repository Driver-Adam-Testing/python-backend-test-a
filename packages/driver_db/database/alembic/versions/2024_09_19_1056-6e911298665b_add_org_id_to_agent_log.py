"""add org_id to agent log

Revision ID: 6e911298665b
Revises: 8d00c01b5759
Create Date: 2024-09-19 10:56:43.283186

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "6e911298665b"
down_revision = "8d00c01b5759"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "runtimelogagentinstance",
        sa.Column("organization_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )

    # Populate the organization_id from the runtimelogagentinstance's workspace's organization_id
    op.execute("""
        UPDATE runtimelogagentinstance
        SET organization_id = (
            SELECT organization_id
            FROM workspaces
            WHERE CAST(workspaces.id AS TEXT) = runtimelogagentinstance.workspace_id
        )
    """)


def downgrade():
    op.drop_column("runtimelogagentinstance", "organization_id")
