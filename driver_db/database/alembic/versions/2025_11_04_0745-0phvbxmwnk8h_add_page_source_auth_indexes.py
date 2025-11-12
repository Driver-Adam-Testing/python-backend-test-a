"""add page source auth indexes

Revision ID: 0phvbxmwnk8h
Revises: a1b2c3d4e5f6
Create Date: 2025-11-04 07:45:00.000000

"""

from alembic import op

revision = "0phvbxmwnk8h"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add indexes to optimize page source authorization queries.

    These indexes speed up the page_source_authorization_filter() which checks
    that users have grants to all sources for a page.
    """
    # for looking up all sources for a page
    op.create_index(
        "ix_document_source_page_node_id",
        "document_source",
        ["page_node_id"],
        unique=False,
    )

    # for traversing from document_source to source nodes
    op.create_index(
        "ix_document_source_source_node_id",
        "document_source",
        ["source_node_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove page source authorization indexes."""
    op.drop_index("ix_document_source_source_node_id", table_name="document_source")
    op.drop_index("ix_document_source_page_node_id", table_name="document_source")
