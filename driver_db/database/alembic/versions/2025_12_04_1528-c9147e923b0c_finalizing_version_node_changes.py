"""finalizing_version_node_changes

Revision ID: c9147e923b0c
Revises: 83650d298b58
Create Date: 2025-12-04 15:28:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c9147e923b0c"
down_revision = "83650d298b58"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # AutoDocStatusHistory
    op.alter_column(
        "autodoc_status_history",
        "source_version_node_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.drop_index(
        "ix_v2_autodoc_status_history_page_node_id", table_name="autodoc_status_history"
    )
    op.create_index(
        op.f("ix_autodoc_status_history_source_version_node_id"),
        "autodoc_status_history",
        ["source_version_node_id"],
        unique=False,
    )
    op.drop_constraint(
        "autodoc_status_history_page_node_id_fkey",
        "autodoc_status_history",
        type_="foreignkey",
    )
    op.drop_column("autodoc_status_history", "page_node_id")

    # ChunkAndEmbedding
    op.add_column(
        "chunk_and_embedding", sa.Column("organization_id", sa.String(), nullable=True)
    )

    # DerivedContent
    op.execute("DELETE FROM derived_content WHERE node_id IS NULL")
    op.alter_column(
        "derived_content", "node_id", existing_type=sa.UUID(), nullable=False
    )
    op.drop_index("ix_derived_contents_relative_path", table_name="derived_content")
    op.drop_column("derived_content", "relative_path")

    # DocumentSource
    op.alter_column(
        "document_source",
        "source_version_node_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.alter_column(
        "document_source",
        "page_version_node_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.drop_index("ix_document_source_page_node_id", table_name="document_source")
    op.drop_index("ix_document_source_source_node_id", table_name="document_source")
    op.drop_constraint(
        "document_source_page_node_id_fkey", "document_source", type_="foreignkey"
    )
    op.drop_constraint(
        "document_source_source_node_id_fkey", "document_source", type_="foreignkey"
    )
    op.drop_column("document_source", "id")
    op.drop_column("document_source", "source_node_id")
    op.drop_column("document_source", "page_node_id")

    # Node
    op.alter_column("node", "primary_asset_id", existing_type=sa.UUID(), nullable=False)
    op.create_index(op.f("ix_node_source_hash"), "node", ["source_hash"], unique=False)
    op.create_unique_constraint(
        "unique_primary_asset_source_hash", "node", ["primary_asset_id", "source_hash"]
    )
    op.create_check_constraint(
        "check_source_hash_not_null_for_codebase_kinds",
        "node",
        "NOT (kind IN ('CODEBASE_FILE', 'CODEBASE_DIRECTORY') AND source_hash IS NULL)",
    )
    op.drop_index("idx_node_version_id_relative_path_length", table_name="node")
    op.drop_index("ix_node_version_id_relative_path_pattern_ops", table_name="node")
    op.drop_index("ix_v2_node_depth", table_name="node")
    op.drop_index("ix_v2_node_relative_path", table_name="node")
    op.drop_index("ix_v2_node_total_files", table_name="node")
    op.drop_index("ix_v2_node_version_id", table_name="node")
    op.drop_constraint("v2_node_version_id_fkey", "node", type_="foreignkey")
    op.drop_column("node", "total_files")
    op.drop_column("node", "misc_metadata")
    op.drop_column("node", "depth")
    op.drop_column("node", "relative_path")
    op.drop_column("node", "version_id")

    # VersionNode
    op.create_index(
        op.f("ix_version_node_node_id"), "version_node", ["node_id"], unique=False
    )
    op.create_index(
        "ix_version_node_version_id_relative_path_length",
        "version_node",
        ["version_id", sa.literal_column("length('relative_path')")],
        unique=False,
    )
    op.create_index(
        "ix_version_node_version_id_relative_path_pattern_ops",
        "version_node",
        ["version_id"],
        unique=False,
        postgresql_ops={"relative_path": "text_pattern_ops"},
    )
    op.create_index(
        op.f("ix_version_node_total_files"),
        "version_node",
        ["total_files"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # VersionNode
    op.drop_index(op.f("ix_version_node_total_files"), table_name="version_node")
    op.drop_index(
        "ix_version_node_version_id_relative_path_pattern_ops",
        table_name="version_node",
        postgresql_ops={"relative_path": "text_pattern_ops"},
    )
    op.drop_index(
        "ix_version_node_version_id_relative_path_length", table_name="version_node"
    )
    op.drop_index(op.f("ix_version_node_node_id"), table_name="version_node")

    # Node
    op.add_column(
        "node", sa.Column("version_id", sa.UUID(), autoincrement=False, nullable=False)
    )
    op.add_column(
        "node",
        sa.Column("relative_path", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "node",
        sa.Column(
            "depth",
            sa.INTEGER(),
            sa.Computed(
                "(length(TRIM(TRAILING '/'::text FROM relative_path)) - length(replace(TRIM(TRAILING '/'::text FROM relative_path), '/'::text, ''::text)))",
                persisted=True,
            ),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "node",
        sa.Column(
            "misc_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "node",
        sa.Column(
            "total_files",
            sa.INTEGER(),
            sa.Computed(
                "((misc_metadata ->> 'total_files'::text))::integer", persisted=True
            ),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "v2_node_version_id_fkey",
        "node",
        "version",
        ["version_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_v2_node_version_id", "node", ["version_id"], unique=False)
    op.create_index("ix_v2_node_total_files", "node", ["total_files"], unique=False)
    op.create_index("ix_v2_node_relative_path", "node", ["relative_path"], unique=False)
    op.create_index("ix_v2_node_depth", "node", ["depth"], unique=False)
    op.create_index(
        "ix_node_version_id_relative_path_pattern_ops",
        "node",
        ["version_id"],
        unique=False,
    )
    op.create_index(
        "idx_node_version_id_relative_path_length",
        "node",
        ["version_id", sa.literal_column("length('relative_path'::text)")],
        unique=False,
    )
    op.alter_column("node", "primary_asset_id", existing_type=sa.UUID(), nullable=True)
    op.drop_check_constraint("check_source_hash_not_null_for_codebase_kinds", "node")
    op.drop_constraint("unique_primary_asset_source_hash", "node", type_="unique")
    op.drop_index(op.f("ix_node_source_hash"), table_name="node")

    # DocumentSource
    op.add_column(
        "document_source",
        sa.Column("page_node_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "document_source",
        sa.Column("source_node_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "document_source",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
    )
    op.create_foreign_key(
        "document_source_source_node_id_fkey",
        "document_source",
        "node",
        ["source_node_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "document_source_page_node_id_fkey",
        "document_source",
        "node",
        ["page_node_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_document_source_source_node_id",
        "document_source",
        ["source_node_id"],
        unique=False,
    )
    op.create_index(
        "ix_document_source_page_node_id",
        "document_source",
        ["page_node_id"],
        unique=False,
    )
    op.alter_column(
        "document_source",
        "page_version_node_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    op.alter_column(
        "document_source",
        "source_version_node_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

    # DerivedContent
    op.add_column(
        "derived_content",
        sa.Column("relative_path", sa.TEXT(), autoincrement=False, nullable=False),
    )
    op.create_index(
        "ix_derived_contents_relative_path",
        "derived_content",
        ["relative_path"],
        unique=False,
    )
    op.alter_column(
        "derived_content", "node_id", existing_type=sa.UUID(), nullable=True
    )

    # ChunkAndEmbedding
    op.drop_column("chunk_and_embedding", "organization_id")

    # AutoDocStatusHistory
    op.add_column(
        "autodoc_status_history",
        sa.Column("page_node_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "autodoc_status_history_page_node_id_fkey",
        "autodoc_status_history",
        "node",
        ["page_node_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_index(
        op.f("ix_autodoc_status_history_source_version_node_id"),
        table_name="autodoc_status_history",
    )
    op.create_index(
        "ix_v2_autodoc_status_history_page_node_id",
        "autodoc_status_history",
        ["page_node_id"],
        unique=False,
    )
    op.alter_column(
        "autodoc_status_history",
        "source_version_node_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    # ### end Alembic commands ###
