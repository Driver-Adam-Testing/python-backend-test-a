"""rename sct,dct id cols

Revision ID: ca49df8b5300
Revises: f53a520edbe0
Create Date: 2024-07-24 08:30:55.614657

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "ca49df8b5300"
down_revision = "f53a520edbe0"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "source_contents", "source_content_type_id", new_column_name="content_type_id"
    )
    op.alter_column(
        "derived_contents", "derived_content_type_id", new_column_name="content_type_id"
    )


def downgrade():
    op.alter_column(
        "source_contents", "content_type_id", new_column_name="source_content_type_id"
    )
    op.alter_column(
        "derived_contents", "content_type_id", new_column_name="derived_content_type_id"
    )
