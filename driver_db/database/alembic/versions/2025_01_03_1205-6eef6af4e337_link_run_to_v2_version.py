"""Link run to v2 version

Revision ID: 6eef6af4e337
Revises: 31e02efc741d
Create Date: 2025-01-03 12:05:16.460100

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "6eef6af4e337"
down_revision = "31e02efc741d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM inspectorrun ir
               WHERE ir.id in(
                     SELECT ir2.id
                     FROM inspectorrun ir2
                     LEFT JOIN v2_version v2
                     ON v2.id = ir.inspection_version_id
                     WHERE v2.id IS NULL
               )
    """)
    op.execute("""
        DELETE FROM inspection_versions iv
                WHERE iv.id in(
                        SELECT iv2.id
                        FROM inspection_versions iv2
                        JOIN inspectorrun ir
                        on iv2.id = ir.inspection_version_id
                        LEFT JOIN v2_version v2
                        ON v2.id = iv2.id
                        WHERE v2.id IS NULL
                )
    """)
    op.execute("""
        UPDATE inspectorrun
        SET version_id = inspection_version_id
    """)


def downgrade() -> None:
    pass
