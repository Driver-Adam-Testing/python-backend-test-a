from collections.abc import Generator
from unittest.mock import Mock

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.api.auth import UserToken

# ============================================================================
# Integration Test Database Fixtures
# ============================================================================
# These fixtures use a PostgreSQL test database for safe, isolated integration testing
# They are ONLY used when tests are marked with @pytest.mark.integration
# ============================================================================


@pytest.fixture(scope="function")
def integration_db_engine() -> Generator[Engine, None, None]:
    """
    Create a PostgreSQL engine for integration tests using a test schema.

    This is SAFE because:
    - Uses a dedicated test schema (rbac_test_schema_<timestamp>)
    - Schema is isolated from main database
    - Schema is dropped after each test
    - Uses the local development database
    """
    import time

    from database.models import (
        Organization,
        OrgMembership,
        PrimaryAsset,
        PrimaryAssetRoleGrant,
        Team,
        TeamMembership,
        User,
    )

    # Use local PostgreSQL database
    db_url = "postgresql+psycopg2://postgres:12345678@localhost:5432/local_db"

    # Create a unique schema name for this test run
    schema_name = f"rbac_test_{int(time.time() * 1000)}"

    engine = create_engine(db_url, echo=False)  # Set to True for SQL debugging

    # Create the test schema
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        conn.commit()

    # Create tables in the test schema (order matters due to foreign keys)
    tables_to_create = [
        Organization.__table__,
        User.__table__,
        OrgMembership.__table__,
        Team.__table__,
        TeamMembership.__table__,
        PrimaryAsset.__table__,
        PrimaryAssetRoleGrant.__table__,
    ]

    # Set the schema for all tables
    for table in tables_to_create:
        table.schema = schema_name

    # Create all tables in the test schema
    SQLModel.metadata.create_all(engine, tables=tables_to_create)

    # Add CASCADE DELETE for TeamMembership and PrimaryAssetRoleGrant
    with engine.connect() as conn:
        # Drop existing foreign key constraints
        conn.execute(
            text(
                f"""
            ALTER TABLE {schema_name}.team_membership
            DROP CONSTRAINT IF EXISTS team_membership_team_id_fkey CASCADE
        """
            )
        )
        conn.execute(
            text(
                f"""
            ALTER TABLE {schema_name}.primary_asset_role_grant
            DROP CONSTRAINT IF EXISTS primary_asset_role_grant_team_id_fkey CASCADE
        """
            )
        )

        # Re-add with CASCADE DELETE
        conn.execute(
            text(
                f"""
            ALTER TABLE {schema_name}.team_membership
            ADD CONSTRAINT team_membership_team_id_fkey
            FOREIGN KEY (team_id) REFERENCES {schema_name}.team(id) ON DELETE CASCADE
        """
            )
        )
        conn.execute(
            text(
                f"""
            ALTER TABLE {schema_name}.primary_asset_role_grant
            ADD CONSTRAINT primary_asset_role_grant_team_id_fkey
            FOREIGN KEY (team_id) REFERENCES {schema_name}.team(id) ON DELETE CASCADE
        """
            )
        )
        conn.commit()

    # Create test organizations
    with Session(engine) as session:
        test_org = Organization(
            id="test-org-id",
            name="Test Organization",
            display_name="Test Organization",
            org_metadata={},
        )
        session.add(test_org)

        # Also create org-1-id and org-2-id for organization isolation tests
        org1 = Organization(
            id="org-1-id",
            name="Organization 1",
            display_name="Organization 1",
            org_metadata={},
        )
        session.add(org1)

        org2 = Organization(
            id="org-2-id",
            name="Organization 2",
            display_name="Organization 2",
            org_metadata={},
        )
        session.add(org2)

        session.commit()

    yield engine

    # Cleanup: Drop the test schema
    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
        conn.commit()

    # Reset the schema to None for subsequent tests
    for table in tables_to_create:
        table.schema = None

    engine.dispose()


@pytest.fixture(scope="function")
def integration_db_session(
    integration_db_engine: Engine,
) -> Generator[Session, None, None]:
    """
    Create a database session for integration tests.

    Each test gets a fresh in-memory database with all tables created.
    """
    with Session(integration_db_engine) as session:
        yield session


# ============================================================================
# Unit Test Fixtures (Existing - Mocked)
# ============================================================================


@pytest.fixture(scope="function")
def current_user_with_org() -> UserToken:
    current_user = Mock(spec=UserToken)
    current_user.user_id = "test_user_id"
    current_user.organization_id = "test_org_id"
    current_user.organization_name = "test_org_name"
    current_user.is_service_account = False
    return current_user


@pytest.fixture(scope="function")
def current_user_with_other_org() -> UserToken:
    current_user = Mock(spec=UserToken)
    current_user.user_id = "other_test_user_id"
    current_user.organization_id = "other_test_org_id"
    current_user.organization_name = "other_test_org_name"
    current_user.is_service_account = False
    return current_user
