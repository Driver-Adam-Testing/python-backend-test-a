"""rename sc meta col

Revision ID: f53a520edbe0
Revises: cd4811731e2f
Create Date: 2024-07-24 07:38:33.001715

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f53a520edbe0"
down_revision = "cd4811731e2f"
branch_labels = None
depends_on = None


def upgrade():
    # Rename the column 'analysis_metadata' to 'metadata'
    op.alter_column(
        "source_contents",
        "analysis_metadata",
        new_column_name="metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
    )


def downgrade():
    # Rename the column 'metadata' back to 'analysis_metadata'
    op.alter_column(
        "source_contents",
        "metadata",
        new_column_name="analysis_metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
    )
