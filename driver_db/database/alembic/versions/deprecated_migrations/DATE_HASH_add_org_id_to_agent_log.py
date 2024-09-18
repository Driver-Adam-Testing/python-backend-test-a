"""Add Organization ID to the Runtime Log Agent Instance

Revision ID: 9da010aa5233
Revises: FILL_THIS_IN
Create Date: 2024-09-17

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9da010aa5233"
down_revision = ""
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column organization_id to the agent logs
    op.add_column(
        "runtimelogagentinstance",
        sa.Column("organization_id", sa.String(), nullable=True),
    )


def downgrade():
    # Remove the organization_id column if downgrading
    op.drop_column("runtimelogagentinstance", "organization_id")
