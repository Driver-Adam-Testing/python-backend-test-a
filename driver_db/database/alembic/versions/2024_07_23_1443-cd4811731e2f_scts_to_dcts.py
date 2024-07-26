"""scts to dcts

Revision ID: cd4811731e2f
Revises: 4584ad95470d
Create Date: 2024-07-23 14:43:47.377285

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "cd4811731e2f"
down_revision = "4584ad95470d"
branch_labels = None
depends_on = None


def upgrade():
    # Copy rows from source_content_types to derived_content_types
    op.execute(
        """
        INSERT INTO derived_content_types (id, type_name, created_at, updated_at)
        SELECT id, type_name, created_at, updated_at
        FROM source_content_types;
        """
    )


def downgrade():
    # Remove the copied rows from derived_content_types
    op.execute(
        """
        DELETE FROM derived_content_types
        WHERE id IN (SELECT id FROM source_content_types);
        """
    )
