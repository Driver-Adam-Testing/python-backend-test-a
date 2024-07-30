"""Copy SC to DC table

Revision ID: 9fdb9475d8f4
Revises: ccbc4d05e796
Create Date: 2024-07-24 14:09:16.520512

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "9fdb9475d8f4"
down_revision = "ccbc4d05e796"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    INSERT INTO derived_contents (
        id,
        content_type_id,
        workspace_id,
        codebase_id,
        content,
        metadata,
        status,
        created_at,
        updated_at,
        "order",
        relative_path
    )
    SELECT
        id,
        content_type_id,
        workspace_id,
        codebase_id,
        content,
        metadata,
        status,
        created_at,
        updated_at,
        "order",
        relative_path
    FROM
        source_contents;
    """
    )


def downgrade():
    op.execute(
        """
    DELETE FROM derived_contents
    WHERE source_content_id IS NULL;
    """
    )
