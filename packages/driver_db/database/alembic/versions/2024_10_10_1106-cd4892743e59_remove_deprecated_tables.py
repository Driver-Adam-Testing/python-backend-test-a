"""Remove deprecated tables

Revision ID: cd4892743e59
Revises: 5c80dca0c06c
Create Date: 2024-10-10 11:06:58.805121

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "cd4892743e59"
down_revision = "5c80dca0c06c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("runtimelogcontentretrieval")
    op.drop_table("runtimelogagenterror")
    op.drop_index("ix_chunk_content_metadata_id", table_name="chunk")
    op.drop_index(
        "ix_chunk_text_embedding_3_small_vector_l2_ops",
        table_name="chunk",
        postgresql_with={"lists": "50"},
        postgresql_using="ivfflat",
    )
    op.drop_table("chunk")
    op.drop_index("ix_contentmetadata_codebase_id", table_name="contentmetadata")
    op.drop_index("ix_contentmetadata_content_type", table_name="contentmetadata")
    op.drop_index("ix_contentmetadata_relative_path", table_name="contentmetadata")
    op.drop_index("ix_contentmetadata_workspace_id", table_name="contentmetadata")
    op.drop_table("contentmetadata")
    # ### end Alembic commands ###


def downgrade() -> None:
    pass
