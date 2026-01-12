"""cascade_delete_user_references

Revision ID: a03d3f6c9793
Revises: d43723a6dc3c
Create Date: 2025-12-10 11:16:12.260602

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a03d3f6c9793"
down_revision = "d43723a6dc3c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TeamMembership: cascade delete on user_id and team_id
    op.drop_constraint(
        "team_membership_user_id_fkey", "team_membership", type_="foreignkey"
    )
    op.drop_constraint(
        "team_membership_team_id_fkey", "team_membership", type_="foreignkey"
    )
    op.create_foreign_key(
        "team_membership_user_id_fkey",
        "team_membership",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "team_membership_team_id_fkey",
        "team_membership",
        "team",
        ["team_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # PrimaryAssetRoleGrant: cascade delete on user_id and team_id
    op.drop_constraint(
        "primary_asset_role_grant_user_id_fkey",
        "primary_asset_role_grant",
        type_="foreignkey",
    )
    op.drop_constraint(
        "primary_asset_role_grant_team_id_fkey",
        "primary_asset_role_grant",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "primary_asset_role_grant_user_id_fkey",
        "primary_asset_role_grant",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "primary_asset_role_grant_team_id_fkey",
        "primary_asset_role_grant",
        "team",
        ["team_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # OrgMembership: cascade delete on user_id and org_id
    op.drop_constraint(
        "org_membership_user_id_fkey", "org_membership", type_="foreignkey"
    )
    op.drop_constraint(
        "org_membership_org_id_fkey", "org_membership", type_="foreignkey"
    )
    op.create_foreign_key(
        "org_membership_user_id_fkey",
        "org_membership",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "org_membership_org_id_fkey",
        "org_membership",
        "organization",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # TeamMembership: remove cascade
    op.drop_constraint(
        "team_membership_user_id_fkey", "team_membership", type_="foreignkey"
    )
    op.drop_constraint(
        "team_membership_team_id_fkey", "team_membership", type_="foreignkey"
    )
    op.create_foreign_key(
        "team_membership_user_id_fkey",
        "team_membership",
        "user",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "team_membership_team_id_fkey",
        "team_membership",
        "team",
        ["team_id"],
        ["id"],
    )

    # PrimaryAssetRoleGrant: remove cascade
    op.drop_constraint(
        "primary_asset_role_grant_user_id_fkey",
        "primary_asset_role_grant",
        type_="foreignkey",
    )
    op.drop_constraint(
        "primary_asset_role_grant_team_id_fkey",
        "primary_asset_role_grant",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "primary_asset_role_grant_user_id_fkey",
        "primary_asset_role_grant",
        "user",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "primary_asset_role_grant_team_id_fkey",
        "primary_asset_role_grant",
        "team",
        ["team_id"],
        ["id"],
    )

    # OrgMembership: remove cascade
    op.drop_constraint(
        "org_membership_user_id_fkey", "org_membership", type_="foreignkey"
    )
    op.drop_constraint(
        "org_membership_org_id_fkey", "org_membership", type_="foreignkey"
    )
    op.create_foreign_key(
        "org_membership_user_id_fkey",
        "org_membership",
        "user",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "org_membership_org_id_fkey",
        "org_membership",
        "organization",
        ["org_id"],
        ["id"],
    )
