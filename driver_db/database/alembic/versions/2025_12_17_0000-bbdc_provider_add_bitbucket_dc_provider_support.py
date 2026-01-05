"""add_bitbucket_dc_provider_support

Revision ID: bbdc_provider
Revises: c9147e923b0c
Create Date: 2025-12-17 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "bbdc_provider"
down_revision = "c9147e923b0c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Bitbucket Data Center to PrimaryAssetProvider enum
    # Note: GitProviderKind.BITBUCKET_DATA_CENTER already exists in the enum
    # Using uppercase to match other enum values (GITHUB, GITLAB_SELF_MANAGED, etc.)
    op.execute("ALTER TYPE primaryassetprovider ADD VALUE 'BITBUCKET_DATA_CENTER'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values
    # This would require recreating the type and all dependent columns
    pass
