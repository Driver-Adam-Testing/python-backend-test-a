"""codebase records to generation-complete

Revision ID: 5c80dca0c06c
Revises: 2641ed3d784a
Create Date: 2024-09-26 09:48:57.186107

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5c80dca0c06c"
down_revision = "2641ed3d784a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    codebase_dc_records_to_generation_complete_update_statement = """
        UPDATE derived_contents SET status = 'generation-complete'
        WHERE content_type_id = (SELECT id FROM derived_content_types WHERE type_name = 'codebase')
        AND codebase_id IN (SELECT id FROM codebases WHERE status = 'processing-complete')
        """
    conn = op.get_bind()
    conn.execute(sa.text(codebase_dc_records_to_generation_complete_update_statement))


def downgrade() -> None:
    pass
