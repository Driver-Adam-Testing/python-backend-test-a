"""add pdf summary

Revision ID: aac18a90e4e3
Revises: b133aee202aa
Create Date: 2024-07-10 13:08:19.076249

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aac18a90e4e3"
down_revision: str | None = "b133aee202aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE contenttype ADD VALUE 'PDF_SUMMARY'")


def downgrade() -> None:
    pass
