"""add_default_source_visibility_to_organization

Revision ID: 089bfda3873b
Revises: 961186cd13c2
Create Date: 2025-11-10 15:33:33.385086

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "089bfda3873b"
down_revision = "961186cd13c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type first
    op.execute("CREATE TYPE sourcevisibility AS ENUM ('private', 'internal', 'public')")

    # Add column with nullable=True first
    op.add_column(
        "organization",
        sa.Column(
            "default_source_visibility",
            sa.Enum(
                "private",
                "internal",
                "public",
                name="sourcevisibility",
                create_type=False,
            ),
            nullable=True,
        ),
    )

    # Update existing organizations to 'internal' to preserve current behavior
    op.execute("UPDATE organization SET default_source_visibility = 'internal'")

    # Make column non-nullable with server_default
    op.alter_column(
        "organization",
        "default_source_visibility",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("organization", "default_source_visibility")
    op.execute("DROP TYPE IF EXISTS sourcevisibility")
