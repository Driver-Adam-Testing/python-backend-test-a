"""Add ts_vector to the chunk and embedding table

Revision ID: 8d00c01b5759
Revises: 54fb48ccdd81
Create Date: 2024-09-17

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8d00c01b5759"
down_revision = "54fb48ccdd81"
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column with the generated tsvector
    op.execute(
        """
        ALTER TABLE chunkandembedding
        ADD COLUMN __ts_vector__ tsvector
        GENERATED ALWAYS AS (
            to_tsvector(
                'english',
                chunkandembedding.text
            )
        ) STORED;
        """
    )


def downgrade():
    # Remove the __ts_vector__ column if downgrading
    op.execute(
        """
        ALTER TABLE chunkandembedding
        DROP COLUMN __ts_vector__;
        """
    )
