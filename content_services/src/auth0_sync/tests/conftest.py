"""
Integration test fixtures for auth0_sync service.

Uses Testcontainers to provision isolated PostgreSQL containers for real DB testing.
Auth0 service is mocked since we can't call real Auth0 in tests.

WARNING: This test setup needs review and cleanup.
See https://linear.app/driver-ai/issue/PE-3183/clean-up-integration-test-db-setup-use-alembic-migrations
This should be refactored to use a cleaner pattern for test DB setup.
"""

import sys
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

# Add src directory to path so 'config' module can be imported
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from database.models import (  # noqa: E402
    Organization,
    OrgMembership,
    PrimaryAsset,
    PrimaryAssetRoleGrant,
    Team,
    TeamMembership,
    User,
)
from database.models_enums import (  # noqa: E402
    OrgRole,
    PrimaryAssetKind,
    PrimaryAssetProvider,
    PrimaryAssetRole,
    PrincipalKind,
    TeamRole,
)
from sqlalchemy.engine import Engine  # noqa: E402
from sqlmodel import Session, create_engine  # noqa: E402
from testcontainers.postgres import PostgresContainer  # noqa: E402

# ============================================================================
# Database Fixtures
# ============================================================================


def run_alembic_migrations(db_url: str) -> None:
    """Run Alembic migrations against the given database URL."""
    # Find the alembic.ini in driver_db
    driver_db_path = (
        Path(__file__).resolve().parent.parent.parent.parent / "packages" / "driver_db" / "database"
    )
    alembic_ini_path = driver_db_path / "alembic.ini"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini_path}")

    # Patch the settings object directly so alembic's env.py uses our test database
    from database import config as db_config

    original_db_url = db_config.settings.DATABASE_URL
    db_config.settings.DATABASE_URL = db_url

    try:
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("script_location", str(driver_db_path / "alembic"))
        command.upgrade(alembic_cfg, "head")
    finally:
        db_config.settings.DATABASE_URL = original_db_url


@pytest.fixture(scope="function")
def integration_db_engine() -> Generator[Engine, None, None]:
    """
    Create a PostgreSQL engine using Testcontainers.

    Each test gets a fresh PostgreSQL container with schema created via Alembic migrations.
    Uses pgvector/pgvector image which includes the vector extension needed by migrations.
    """
    postgres = PostgresContainer("pgvector/pgvector:pg16")
    postgres.start()

    db_url = postgres.get_connection_url()
    engine = create_engine(db_url, echo=False)

    # Run Alembic migrations to create schema
    run_alembic_migrations(db_url)

    # Pre-create test organizations
    with Session(engine) as session:
        test_org = Organization(
            id="test-org-id",
            name="Test Organization",
            display_name="Test Organization",
            org_metadata={},
        )
        org1 = Organization(
            id="org-1-id",
            name="Organization 1",
            display_name="Organization 1",
            org_metadata={},
        )
        org2 = Organization(
            id="org-2-id",
            name="Organization 2",
            display_name="Organization 2",
            org_metadata={},
        )
        session.add_all([test_org, org1, org2])
        session.commit()

    yield engine

    engine.dispose()
    postgres.stop()


@pytest.fixture(scope="function")
def integration_db_session(
    integration_db_engine: Engine,
) -> Generator[Session, None, None]:
    """Create a database session for integration tests."""
    with Session(integration_db_engine) as session:
        yield session
        session.rollback()


# ============================================================================
# Auth0 Service Mock
# ============================================================================


@pytest.fixture
def mock_auth0_service() -> MagicMock:
    """
    Mock Auth0 service for controlling test scenarios.

    Configure return values in each test to simulate Auth0 state.
    """
    mock = MagicMock()
    # Default: user exists but not in any org
    mock.get_user_organizations.return_value = []
    mock.get_user_profile.return_value = {
        "user_id": "auth0|test",
        "email": "test@example.com",
        "name": "Test User",
        "updated_at": datetime.now(UTC).isoformat(),
        "app_metadata": {},
    }
    mock.get_organization.return_value = {
        "id": "test-org-id",
        "name": "Test Organization",
        "display_name": "Test Organization",
        "metadata": {},
    }
    return mock


@pytest.fixture
def patch_processor(
    integration_db_engine: Engine, mock_auth0_service: MagicMock
) -> Generator[None, None, None]:
    """
    Patch auth0_event_processor to use test DB engine and mock Auth0 service.

    This patches the global `engine` and `auth0_service` in the processor module.
    """
    from event_processor import auth0_event_processor

    with (
        patch.object(auth0_event_processor, "engine", integration_db_engine),
        patch.object(auth0_event_processor, "auth0_service", mock_auth0_service),
    ):
        yield


# ============================================================================
# Factory Helpers
# ============================================================================


class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create(
        session: Session,
        user_id: str | None = None,
        email: str | None = None,
        name: str | None = None,
        organization_id: str = "test-org-id",
        org_role: OrgRole = OrgRole.org_member,
    ) -> User:
        """Create a user and add them to an organization."""
        user_id = user_id or f"auth0|{uuid4().hex[:16]}"
        user = User(
            id=user_id,
            email=email or f"user-{uuid4().hex[:8]}@test.com",
            name=name or f"Test User {uuid4().hex[:8]}",
            created_at=datetime.now(UTC),
            auth0_updated_at=datetime.now(UTC),
        )
        session.add(user)
        session.flush()

        org_membership = OrgMembership(
            id=uuid4(),
            org_id=organization_id,
            user_id=user.id,
            role=org_role,
        )
        session.add(org_membership)
        session.commit()
        session.refresh(user)
        return user


class TeamFactory:
    """Factory for creating test teams."""

    @staticmethod
    def create(
        session: Session,
        name: str | None = None,
        organization_id: str = "test-org-id",
    ) -> Team:
        """Create a team."""
        team = Team(
            id=uuid4(),
            name=name or f"Test Team {uuid4().hex[:8]}",
            organization_id=organization_id,
        )
        session.add(team)
        session.commit()
        session.refresh(team)
        return team


class TeamMembershipFactory:
    """Factory for creating team memberships."""

    @staticmethod
    def create(
        session: Session,
        team_id: UUID,
        user_id: str,
        role: TeamRole = TeamRole.team_member,
    ) -> TeamMembership:
        """Create a team membership."""
        membership = TeamMembership(
            id=uuid4(),
            team_id=team_id,
            user_id=user_id,
            role=role,
        )
        session.add(membership)
        session.commit()
        session.refresh(membership)
        return membership


class PrimaryAssetFactory:
    """Factory for creating test assets (sources)."""

    @staticmethod
    def create(
        session: Session,
        display_name: str | None = None,
        organization_id: str = "test-org-id",
    ) -> PrimaryAsset:
        """Create a primary asset."""
        asset = PrimaryAsset(
            id=uuid4(),
            display_name=display_name or f"Test Source {uuid4().hex[:8]}",
            kind=PrimaryAssetKind.CODEBASE,
            provider=PrimaryAssetProvider.USER,
            organization_id=organization_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
        return asset


class PrimaryAssetRoleGrantFactory:
    """Factory for creating access grants."""

    @staticmethod
    def create(
        session: Session,
        primary_asset_id: UUID,
        organization_id: str = "test-org-id",
        principal_kind: PrincipalKind = PrincipalKind.user,
        role: PrimaryAssetRole = PrimaryAssetRole.asset_member,
        user_id: str | None = None,
        team_id: UUID | None = None,
    ) -> PrimaryAssetRoleGrant:
        """Create an access grant."""
        grant = PrimaryAssetRoleGrant(
            id=uuid4(),
            primary_asset_id=primary_asset_id,
            organization_id=organization_id,
            principal_kind=principal_kind,
            role=role,
            user_id=user_id,
            team_id=team_id,
            created_at=datetime.now(UTC),
        )
        session.add(grant)
        session.commit()
        session.refresh(grant)
        return grant


class OrgMembershipFactory:
    """Factory for creating org memberships directly."""

    @staticmethod
    def create(
        session: Session,
        user_id: str,
        org_id: str,
        role: OrgRole = OrgRole.org_member,
    ) -> OrgMembership:
        """Create an org membership."""
        membership = OrgMembership(
            id=uuid4(),
            user_id=user_id,
            org_id=org_id,
            role=role,
        )
        session.add(membership)
        session.commit()
        session.refresh(membership)
        return membership
