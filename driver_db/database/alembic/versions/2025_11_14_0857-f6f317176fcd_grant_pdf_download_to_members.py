"""grant_pdf_download_to_members

Revision ID: f6f317176fcd
Revises: 089bfda3873b
Create Date: 2025-11-14 08:57:17.805813

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f6f317176fcd"
down_revision = "089bfda3873b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO role_action_allow_asset (id, role, action_key) VALUES
        ('282e4e7a-d10a-42ad-80a4-6a9aef1947ad', 'asset_member', 'pdf.download')
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM role_action_allow_asset
        WHERE id = '282e4e7a-d10a-42ad-80a4-6a9aef1947ad'
    """)
