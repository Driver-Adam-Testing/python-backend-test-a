"""Strs to enum content kind

Revision ID: 68808e67d224
Revises: 047a6ed8fdaa
Create Date: 2025-01-07 12:11:30.477387

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "68808e67d224"
down_revision = "047a6ed8fdaa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE contentkind AS ENUM (
            'pdf-visual-summary',
            'pdf-text-summary',
            'pdf-image-summary',
            'pdf-extracted-text',
            'pdf-extracted-table',
            'template',
            'short_paragraph_description',
            'terse_sentence_description',
            'long_description',
            'quick_start_entry',
            'quick_start_getting_started',
            'quick_start_dependencies',
            'quick_start_use',
            'architecture_diagram',
            'chunk_descriptions',
            'application_note',
            'short_sentence_description',
            'symbol',
            'pdf_summary',
            'codebase',
            'codebase-directory',
            'codebase-file',
            'supplemental-document',
            'TOP_LEVEL_SHORT_SENTENCE',
            'TOP_LEVEL_SHORT_PARAGRAPH',
            'TOP_LEVEL_TERSE_SENTENCE',
            'TOP_LEVEL_LONG_DESCRIPTION'
        )
        """
    )

    op.execute(
        """
        ALTER TABLE derived_contents
        ALTER COLUMN content_kind TYPE contentkind
        USING content_kind::contentkind
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE derived_contents
        ALTER COLUMN content_kind TYPE TEXT
        USING content_kind::TEXT
        """
    )

    op.execute("DROP TYPE contentkind")
