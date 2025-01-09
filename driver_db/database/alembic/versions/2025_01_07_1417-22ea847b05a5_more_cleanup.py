"""More cleanup

Revision ID: 22ea847b05a5
Revises: 68808e67d224
Create Date: 2025-01-07 14:17:04.876622

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "22ea847b05a5"
down_revision = "68808e67d224"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "v2_node",
        "relative_path",
        existing_type=sa.TEXT(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "v2_node",
        "relative_path",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.TEXT(),
        existing_nullable=False,
    )
