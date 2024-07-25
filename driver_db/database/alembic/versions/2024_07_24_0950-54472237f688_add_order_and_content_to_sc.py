"""Add order and content to sc

Revision ID: 54472237f688
Revises: ca49df8b5300
Create Date: 2024-07-24 09:50:31.362362

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "54472237f688"
down_revision = "ca49df8b5300"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("source_contents", sa.Column("order", sa.Integer(), nullable=True))
    op.add_column("source_contents", sa.Column("content", sa.Text(), nullable=True))
    # After renaming, indices changed
    op.drop_index(
        "ix_source_contents_source_content_type_id", table_name="source_contents"
    )
    op.create_index(
        op.f("ix_source_contents_content_type_id"),
        "source_contents",
        ["content_type_id"],
        unique=False,
    )

    # Set server default for future inserts to 0
    op.alter_column(
        "source_contents",
        "order",
        server_default=sa.text("0"),
        existing_type=sa.Integer,
    )
    # ### end Alembic commands ###


def downgrade():
    # TODO this may have bugs
    op.drop_index(
        op.f("ix_source_contents_content_type_id"), table_name="source_contents"
    )
    op.create_index(
        "ix_source_contents_source_content_type_id",
        "source_contents",
        ["content_type_id"],
        unique=False,
    )
    op.drop_column("source_contents", "content")
    op.drop_column("source_contents", "order")
