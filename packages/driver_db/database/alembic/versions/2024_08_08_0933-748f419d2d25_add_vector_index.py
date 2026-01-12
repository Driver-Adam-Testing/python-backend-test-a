"""Add vector index

Revision ID: 748f419d2d25
Revises: ba2204f9ebda
Create Date: 2024-08-08 09:33:27.324411

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "748f419d2d25"
down_revision = "ba2204f9ebda"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunk_text_embedding_3_small_vector_l2_ops ON chunk USING ivfflat (text_embedding_3_small vector_l2_ops) WITH (lists = 50);"
    )


def downgrade():
    op.drop_index(
        op.f("ix_chunk_text_embedding_3_small_vector_l2_ops"), table_name="chunk"
    )
