"""make_organization_auth0_updated_at_nullable

Revision ID: 3ca3767a91bf
Revises: c413495a4a23
Create Date: 2025-10-09 14:11:15.522441

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3ca3767a91bf"
down_revision = "c413495a4a23"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make organization.auth0_updated_at nullable since Auth0 doesn't provide updated_at for orgs
    op.alter_column(
        "organization",
        "auth0_updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    # Revert to non-nullable
    op.alter_column(
        "organization",
        "auth0_updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
