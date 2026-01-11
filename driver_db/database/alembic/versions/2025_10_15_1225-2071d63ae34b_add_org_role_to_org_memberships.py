"""add org role to org memberships

Revision ID: 2071d63ae34b
Revises: 3ca3767a91bf
Create Date: 2025-10-15 12:05:53.412901

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2071d63ae34b"
down_revision = "3ca3767a91bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type first
    op.execute("CREATE TYPE orgrole AS ENUM ('super_admin', 'member')")
    op.add_column(
        "org_membership",
        sa.Column(
            "role",
            sa.Enum("super_admin", "member", name="orgrole", create_type=False),
            nullable=True,
        ),
    )
    op.execute("UPDATE org_membership SET role = 'member'")
    op.alter_column("org_membership", "role", nullable=False)


def downgrade() -> None:
    op.drop_column("org_membership", "role")
    op.execute("DROP TYPE IF EXISTS orgrole")
