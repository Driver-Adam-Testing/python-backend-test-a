"""Add default workspaces

These Default workspaces will be used to hold new content that is scoped to the 
entire organization. It may also be used as the first data migration stop
when we get to removing the workspace table from our DB entirely 
(N workspaces -> this Default workspace -> No workspace table)

Revision ID: d858e8f1ee5e
Revises: fe4618de915c
Create Date: 2024-08-02 08:58:55.922140

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d858e8f1ee5e"
down_revision = "fe4618de915c"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        insert into workspaces (
            organization_id,
            display_name,
            description,
            updated_at
        ) select distinct organization_id, 'Default', 'Default', now() from workspaces
        """
    )


def downgrade():
    op.execute(
        """
        delete from workspaces where display_name = 'Default'
        """
    )
