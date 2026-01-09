"""Add API User
Revision ID: 8f59b93a989f
Revises:
Create Date: 2024-10-16 08:48:47.819363
"""

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "8f59b93a989f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    new_api_user = os.environ.get("NEW_API_USERNAME")
    new_api_password = os.environ.get("NEW_API_PASSWORD")
    db_name = os.environ.get("POSTGRES_DB")
    if not new_api_user or not new_api_password:
        print(
            "Environment variables NEW_API_USERNAME or NEW_API_PASSWORD are not set, skipping user creation."
        )
        return

    op.execute(
        f"""
        DO $$ BEGIN
            IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{new_api_user}') THEN
                RAISE NOTICE 'User {new_api_user} already exists.';
            ELSE
                CREATE USER {new_api_user} WITH PASSWORD '{new_api_password}';
                GRANT CONNECT ON DATABASE {db_name} TO {new_api_user};
                GRANT USAGE ON SCHEMA public TO {new_api_user};
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {new_api_user};
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {new_api_user};
                ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {new_api_user};
                ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {new_api_user};
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    pass
