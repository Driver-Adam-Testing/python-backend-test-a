"""rename enum values with prefixes

Revision ID: a1b2c3d4e5f6
Revises: 4060b23411c9
Create Date: 2025-10-30 16:10:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "4060b23411c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename PrimaryAssetRole enum values
    op.execute("ALTER TYPE primaryassetrole RENAME VALUE 'admin' TO 'asset_admin'")
    op.execute("ALTER TYPE primaryassetrole RENAME VALUE 'viewer' TO 'asset_viewer'")

    # Rename TeamRole enum values
    op.execute("ALTER TYPE teamrole RENAME VALUE 'member' TO 'team_member'")

    # Rename OrgRole enum values
    op.execute("ALTER TYPE orgrole RENAME VALUE 'super_admin' TO 'org_super_admin'")
    op.execute("ALTER TYPE orgrole RENAME VALUE 'member' TO 'org_member'")

    # Update the check constraint to use new enum value
    op.execute(
        "ALTER TABLE primary_asset_role_grant DROP CONSTRAINT chk_org_public_view_only"
    )
    op.execute(
        "ALTER TABLE primary_asset_role_grant ADD CONSTRAINT chk_org_public_view_only "
        "CHECK (principal_kind NOT IN ('org','public') OR role = 'asset_viewer')"
    )


def downgrade() -> None:
    # Revert check constraint
    op.execute(
        "ALTER TABLE primary_asset_role_grant DROP CONSTRAINT chk_org_public_view_only"
    )
    op.execute(
        "ALTER TABLE primary_asset_role_grant ADD CONSTRAINT chk_org_public_view_only "
        "CHECK (principal_kind NOT IN ('org','public') OR role = 'viewer')"
    )

    # Revert OrgRole enum values
    op.execute("ALTER TYPE orgrole RENAME VALUE 'org_member' TO 'member'")
    op.execute("ALTER TYPE orgrole RENAME VALUE 'org_super_admin' TO 'super_admin'")

    # Revert TeamRole enum values
    op.execute("ALTER TYPE teamrole RENAME VALUE 'team_member' TO 'member'")

    # Revert PrimaryAssetRole enum values
    op.execute("ALTER TYPE primaryassetrole RENAME VALUE 'asset_viewer' TO 'viewer'")
    op.execute("ALTER TYPE primaryassetrole RENAME VALUE 'asset_admin' TO 'admin'")
