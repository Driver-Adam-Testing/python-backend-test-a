"""Copy codebase id to all DC using SC

Revision ID: cbd25d8d71ff
Revises: 9ce7977fdcb5
Create Date: 2024-07-25 10:41:40.618865

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "cbd25d8d71ff"
down_revision = "9ce7977fdcb5"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    WITH SourceCodebase AS (
        SELECT
            d1.id AS derived_content_id,
            d2.codebase_id AS source_codebase_id
        FROM
            derived_contents d1
        JOIN
            derived_contents d2
        ON
            d1.source_content_id = d2.id
        WHERE
            d1.source_content_id IS NOT NULL
    )
    UPDATE derived_contents
    SET
        codebase_id = sc.source_codebase_id
    FROM
        SourceCodebase sc
    WHERE
        derived_contents.id = sc.derived_content_id;
    """
    )


def downgrade():
    pass
