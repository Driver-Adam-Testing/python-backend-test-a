"""Add content_name to derived_content

Revision ID: c3c66c4c4201
Revises: 5a533a6716b2
Create Date: 2024-09-10 08:43:32.957046

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3c66c4c4201"
down_revision = "5a533a6716b2"
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column to the derived_contents table
    op.add_column(
        "derived_contents", sa.Column("content_name", sa.Text(), nullable=True)
    )
    # Create an index for the new column
    op.create_index(
        "ix_derived_contents_content_name", "derived_contents", ["content_name"]
    )


def downgrade():
    # Remove the index if downgrading
    op.drop_index("ix_derived_contents_content_name", table_name="derived_contents")
    # Remove the column if downgrading
    op.drop_column("derived_contents", "content_name")
