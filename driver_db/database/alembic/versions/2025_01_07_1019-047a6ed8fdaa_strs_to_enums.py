"""Strs to enums

Revision ID: 047a6ed8fdaa
Revises: 4c5c3428bf03
Create Date: 2025-01-07 10:19:32.512733

"""

from alembic import op

revision = "047a6ed8fdaa"
down_revision = "4c5c3428bf03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE primaryassetkind AS ENUM ('CODEBASE', 'FILE', 'PAGE', 'PAGE_TEMPLATE')"
    )
    op.execute(
        "CREATE TYPE versionstatus AS ENUM ('GENERATING', 'GENERATION_COMPLETE', 'GENERATION_ERROR')"
    )

    # Update data in v2_version to replace '-' with '_'. This is NOT reverted in the downgrade because it was a
    # migration bug.
    op.execute(
        """
        UPDATE v2_version
        SET status = REPLACE(status, '-', '_')
        """
    )

    # Alter columns with USING clause to cast values
    op.execute(
        """
        ALTER TABLE v2_primary_asset
        ALTER COLUMN kind TYPE primaryassetkind
        USING kind::primaryassetkind
        """
    )
    op.execute(
        """
        ALTER TABLE v2_version
        ALTER COLUMN status TYPE versionstatus
        USING status::versionstatus
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE v2_version
        ALTER COLUMN status TYPE VARCHAR
        USING status::TEXT
        """
    )
    op.execute(
        """
        ALTER TABLE v2_primary_asset
        ALTER COLUMN kind TYPE VARCHAR
        USING kind::TEXT
        """
    )

    # Drop enum types
    op.execute("DROP TYPE versionstatus")
    op.execute("DROP TYPE primaryassetkind")
