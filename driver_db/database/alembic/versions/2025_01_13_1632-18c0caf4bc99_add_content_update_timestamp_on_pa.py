"""Add content update timestamp on PA

Revision ID: 18c0caf4bc99
Revises: 57be28321d1c
Create Date: 2025-01-13 16:32:09.735701

"""

import textwrap

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "18c0caf4bc99"
down_revision = "57be28321d1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "v2_primary_asset",
        sa.Column(
            "related_content_last_updated",
            sa.DateTime(timezone=True),
            nullable=True,  # TODO add a way to populate this...
        ),
    )
    op.execute(
        textwrap.dedent("""
        UPDATE v2_primary_asset
        SET related_content_last_updated = '1970-01-01 00:00:00+00'
        WHERE related_content_last_updated IS NULL;

        -- update related_content_last_updated with the latest content timestamp for each primary asset
        WITH latest_content_updates AS (
            SELECT
                pa.id as primary_asset_id,
                MAX(dc.updated_at) as latest_content_update
            FROM v2_primary_asset pa
            JOIN v2_version v ON v.primary_asset_id = pa.id
            JOIN v2_node n ON n.version_id = v.id
            JOIN derived_contents dc ON dc.node_id = n.id
            GROUP BY pa.id
        )
        UPDATE v2_primary_asset pa
        SET related_content_last_updated = lcu.latest_content_update
        FROM latest_content_updates lcu
        WHERE pa.id = lcu.primary_asset_id
        AND lcu.latest_content_update > pa.related_content_last_updated;
        """)
    )


def downgrade() -> None:
    op.drop_column("v2_primary_asset", "related_content_last_updated")
