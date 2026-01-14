"""connected status on version

Revision ID: 451bf2d9113c
Revises: 25d3fa4abdc5
Create Date: 2025-01-23 09:19:33.564478

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "451bf2d9113c"
down_revision = "25d3fa4abdc5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE versionstatus ADD VALUE 'CONNECTED'")


def downgrade() -> None:
    # No straightforward way to remove an enum value in Postgres
    # Used example in accepted answer here: https://stackoverflow.com/questions/25811017/how-to-delete-an-enum-type-value-in-postgres
    op.execute(
        "CREATE TYPE versionstatus_new AS ENUM ('GENERATING', 'GENERATION_COMPLETE', 'GENERATION_ERROR')"
    )
    op.execute(
        """
        UPDATE v2_version
        SET status = 'GENERATION_ERROR'
        WHERE status = 'CONNECTED'
        """
    )
    op.execute(
        """
        ALTER TABLE v2_version
        ALTER COLUMN status TYPE versionstatus_new
        USING status::text::versionstatus_new
        """
    )
    op.execute("DROP TYPE versionstatus")
    op.execute("ALTER TYPE versionstatus_new RENAME TO versionstatus")
