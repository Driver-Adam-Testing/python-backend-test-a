"""Add rel path to sc

Revision ID: 3844d00aa769
Revises: 54472237f688
Create Date: 2024-07-24 10:18:30.734745

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3844d00aa769"
down_revision = "54472237f688"
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add the column with a temporary default value
    op.add_column(
        "derived_contents",
        sa.Column("relative_path", sa.Text(), nullable=False, server_default=""),
    )

    # Step 2: Populate relative_path using the related source_content
    op.execute(
        """
        UPDATE derived_contents
        SET relative_path = (
            SELECT sc.relative_path
            FROM source_contents sc
            WHERE sc.id = derived_contents.source_content_id
        )
    """
    )

    # Step 3: Drop the temporary default value
    op.alter_column("derived_contents", "relative_path", server_default=None)


def downgrade():
    op.drop_column("derived_contents", "relative_path")
