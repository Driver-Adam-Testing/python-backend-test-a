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
    # Add the index for the __ts_vector__ column
    op.create_index(
        "ix_chunkandembedding___ts_vector__",
        "chunkandembedding",
        ["__ts_vector__"],
        postgresql_using="gin",
    )


def downgrade():
    # Remove the __ts_vector__ column if downgrading
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name='chunkandembedding'
                       AND column_name='__ts_vector__') THEN
                ALTER TABLE chunkandembedding
                DROP COLUMN __ts_vector__;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_indexes
                       WHERE tablename='chunkandembedding'
                       AND indexname='ix_chunkandembedding___ts_vector__') THEN
                DROP INDEX ix_chunkandembedding___ts_vector__;
            END IF;
        END $$;
        """
    )
