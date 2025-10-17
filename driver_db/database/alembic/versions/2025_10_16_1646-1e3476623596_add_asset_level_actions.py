"""add asset level actions

Revision ID: 1e3476623596
Revises: b0a2dca419c5
Create Date: 2025-10-16 16:46:30.105257

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1e3476623596"
down_revision = "b0a2dca419c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO action (key, description) VALUES
        ('codebase.view_versions', 'View versions of a codebase'),
        ('codebase.generate_tech_docs', 'Generate tech docs for a codebase'),
        ('pdf.download', 'Download PDF asset'),
        ('asset.upload', 'Upload zip or pdf asset'),
        ('autodoc.custom_config_upload', 'Upload custom config for autodoc generation'),
        ('asset.use_as_source', 'Use codebase or pdf as a source'),
        ('asset_tag.manage', 'Manage asset tags'),
        ('asset.manage', 'Manage assets'),
        ('asset.delete', 'Delete assets')
    """)

    # Grant asset-level actions to viewers
    op.execute("""
        INSERT INTO role_action_allow_asset (id, role, action_key) VALUES
        ('ff87ab60-cee8-45e6-817e-91c6be73d802', 'viewer', 'codebase.view_versions'),
        ('863dd140-f2ac-431f-867c-301f39550953', 'viewer', 'asset.use_as_source')
    """)

    # Grant asset-level actions to admins
    op.execute("""
        INSERT INTO role_action_allow_asset (id, role, action_key) VALUES
        ('87796dc4-0173-4202-9515-4be1627a0410', 'admin', 'codebase.view_versions'),
        ('f170386a-f4ee-4753-9efa-1da7aa831705', 'admin', 'codebase.generate_tech_docs'),
        ('2f9b6430-ec01-4614-8b42-42c23c659ead', 'admin', 'pdf.download'),
        ('e9895d52-f2cd-4b33-9da4-f14b7793b605', 'admin', 'autodoc.custom_config_upload'),
        ('cbbb0d4c-cdeb-45d5-9bb9-da8993ec354a', 'admin', 'asset.use_as_source'),
        ('46f1c5a0-38f5-4b34-abcf-c9d0c64cc609', 'admin', 'asset_tag.manage'),
        ('4cf6b078-b675-464f-9666-271077ee9cc6', 'admin', 'asset.manage'),
        ('c9121d7a-e008-486a-953a-12bf0e886bfb', 'admin', 'asset.delete')
    """)

    # Grant asset.upload to member role (using static UUID)
    op.execute("""
        INSERT INTO role_action_allow_org (id, role, action_key) VALUES
        ('44b685e5-c5d3-45ae-8c4c-538a6c08cd48', 'member', 'asset.upload')
        ('9f4fd77f-a6b4-4657-9428-d7590b05e159', 'super_admin', 'asset.upload')
    """)


def downgrade() -> None:
    # Remove role mappings
    op.execute("""
        DELETE FROM role_action_allow_org
        WHERE action_key IN ('asset.upload')
    """)
    op.execute("""
        DELETE FROM role_action_allow_asset
        WHERE action_key IN ('codebase.view_versions', 'codebase.generate_tech_docs', 'pdf.download',
                             'asset.upload', 'autodoc.custom_config_upload', 'asset.use_as_source',
                             'asset_tag.manage', 'asset.manage', 'asset.delete')
    """)

    # Remove actions
    op.execute("""
        DELETE FROM action
        WHERE key IN ('codebase.view_versions', 'codebase.generate_tech_docs', 'pdf.download',
                      'asset.upload', 'autodoc.custom_config_upload', 'asset.use_as_source',
                      'asset_tag.manage', 'asset.manage', 'asset.delete')
    """)
