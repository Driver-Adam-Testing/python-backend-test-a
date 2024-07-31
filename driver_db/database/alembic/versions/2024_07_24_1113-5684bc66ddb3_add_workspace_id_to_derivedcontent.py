"""Add workspace_id to DerivedContent

Revision ID: 5684bc66ddb3
Revises: 3844d00aa769
Create Date: 2024-07-24 11:13:49.012056

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "5684bc66ddb3"
down_revision = "3844d00aa769"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "derived_contents",
        sa.Column(
            "workspace_id",
            sqlmodel.sql.sqltypes.GUID(),
            nullable=False,
            server_default="00000000-0000-0000-0000-000000000000",
        ),
    )
    # op.create_foreign_key(None, 'derived_contents', 'workspaces', ['workspace_id'], ['id'])
    # Populate workspace_id
    op.execute(
        """
        UPDATE derived_contents
        SET workspace_id = (
            SELECT sc.workspace_id
            FROM source_contents sc
            WHERE sc.id = derived_contents.source_content_id
        )
    """
    )
    # Drop the temporary default value
    op.alter_column("derived_contents", "workspace_id", server_default=None)


def downgrade():
    # op.drop_constraint(None, 'derived_contents', type_='foreignkey')
    op.drop_column("derived_contents", "workspace_id")
