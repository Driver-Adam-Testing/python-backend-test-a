# Integration Testing with Testcontainers

## Table of Contents
- [Overview](#overview)
- [What is Testcontainers?](#what-is-testcontainers)
- [Why We Use Testcontainers](#why-we-use-testcontainers)
- [How It Works](#how-it-works)
- [Setup and Configuration](#setup-and-configuration)
- [Writing Integration Tests](#writing-integration-tests)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Overview

Our integration tests use **Testcontainers** to provide isolated PostgreSQL database instances for each test. This ensures tests are reproducible, isolated, and run against real database instances rather than mocks.

**Quick Stats:**
- 🐳 Uses Docker containers for PostgreSQL 16
- 🧪 20+ integration tests passing
- ⚡ Each test gets a fresh database
- 🔄 Automatic cleanup after tests complete

---

## What is Testcontainers?

[Testcontainers](https://testcontainers.com/) is an open-source library that provides lightweight, throwaway instances of databases, message queues, web browsers, or anything else that can run in a Docker container.

**Key Features:**
- Spins up Docker containers programmatically
- Automatically cleans up containers after tests
- Supports 50+ pre-built modules (PostgreSQL, MySQL, MongoDB, Redis, etc.)
- Available in 11+ programming languages including Python

---

## Why We Use Testcontainers

### Problems It Solves

**Before Testcontainers:**
```python
# ❌ Complex manual schema management
schema_name = f"rbac_test_{int(time.time() * 1000)}"
# Manual search_path manipulation
conn.execute(text(f"SET search_path TO {schema_name}"))
# Schema conflicts between tests
# ~195 lines of complex setup code
```

**After Testcontainers:**
```python
# ✅ Simple, clean container management
postgres = PostgresContainer("postgres:16-alpine")
postgres.start()
db_url = postgres.get_connection_url()
# ~140 lines of cleaner code
```

### Benefits

| Aspect | Without Testcontainers | With Testcontainers |
|--------|----------------------|-------------------|
| **Isolation** | Schema-based (brittle) | Container-based (true isolation) |
| **Cleanup** | Manual schema dropping | Automatic container removal |
| **Setup** | Complex search_path magic | Simple container start |
| **Conflicts** | Schema name collisions | Impossible (separate containers) |
| **Production Parity** | Same DB, different schemas | Identical fresh DB per test |

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Integration Test                                        │
│  (test_team_service_integration.py)                     │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ uses
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Pytest Fixture: integration_db_session                 │
│  (conftest.py)                                          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ depends on
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Pytest Fixture: integration_db_engine                  │
│  - Starts PostgreSQL container                          │
│  - Creates database schema                              │
│  - Returns SQLAlchemy engine                            │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ manages
                  ↓
┌─────────────────────────────────────────────────────────┐
│  🐳 Docker Container                                    │
│  - postgres:16-alpine                                    │
│  - Fresh database                                        │
│  - Random port mapping                                   │
│  - Auto-removed after test                               │
└─────────────────────────────────────────────────────────┘
```

### Lifecycle

```python
# 1. TEST SETUP (before test runs)
postgres = PostgresContainer("postgres:16-alpine")
postgres.start()  # 🐳 Container starts
# Creates: Fresh PostgreSQL instance on random port
# Time: ~2-3 seconds

# 2. SCHEMA CREATION
engine = create_engine(db_url)
SQLModel.metadata.create_all(engine, tables=tables_to_create)
# Creates: All required database tables
# Time: ~100ms

# 3. TEST EXECUTION
def test_my_feature(integration_db_session):
    # Your test code here with clean database
    pass

# 4. TEST TEARDOWN (after test completes)
postgres.stop()  # 🧹 Container removed automatically
# Cleanup: Complete removal, no leftover data
```

---

## Setup and Configuration

### Prerequisites

**Required:**
- Docker Desktop (or Docker Engine) installed and running
- Python 3.12+
- Poetry for dependency management

**Installation Check:**
```bash
# Verify Docker is running
docker --version
docker ps

# Should see something like:
# Docker version 24.0.0, build xyz
# CONTAINER ID   IMAGE   ...
```

### Dependencies

The required packages are already installed in the project:

```toml
# pyproject.toml
[tool.poetry.group.dev.dependencies]
testcontainers = {version = "^4.13.2", extras = ["postgres"]}
pytest = "^7.4.4"
sqlmodel = "^0.0.21"
```

### Configuration Files

#### 1. Pytest Configuration (`backend/pyproject.toml`)

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests (require PostgreSQL container)",
    # ... other markers
]
```

#### 2. Test Fixtures (`backend/app/conftest.py`)

```python
@pytest.fixture(scope="function")
def integration_db_engine() -> Generator[Engine, None, None]:
    """
    Creates a fresh PostgreSQL container for each test function.

    Lifecycle:
    1. Start PostgreSQL 16 container
    2. Create database schema (tables, constraints)
    3. Insert test organizations
    4. Yield engine to test
    5. Cleanup: Stop and remove container
    """
    # Start container
    postgres = PostgresContainer("postgres:16-alpine")
    postgres.start()

    # Create engine and schema
    db_url = postgres.get_connection_url()
    engine = create_engine(db_url, echo=False)

    # ... schema creation code ...

    yield engine

    # Automatic cleanup
    engine.dispose()
    postgres.stop()


@pytest.fixture(scope="function")
def integration_db_session(
    integration_db_engine: Engine,
) -> Generator[Session, None, None]:
    """
    Provides a database session for tests.

    The session is bound to the Testcontainer PostgreSQL instance.
    """
    with Session(integration_db_engine) as session:
        yield session
        session.rollback()  # Clean rollback after each test
```

---

## Writing Integration Tests

### Basic Test Structure

```python
import pytest
from sqlmodel import Session
from app.services.team_service import TeamService
from app.test_factories import TeamFactory

class TestTeamService:
    """Integration tests for TeamService."""

    @pytest.mark.integration  # ⚠️ Required marker!
    def test_create_team(self, integration_db_session: Session):
        """Test creating a team in the database."""
        # Arrange
        service = TeamService(integration_db_session)
        mock_user = create_mock_user("test-org-id")

        # Act
        team = service.create_team(
            user=mock_user,
            request=CreateTeamRequest(
                name="Engineering Team",
                description="Backend team"
            )
        )

        # Assert
        assert team.name == "Engineering Team"
        assert team.organization_id == "test-org-id"

        # Verify in database
        from database.models import Team
        db_team = integration_db_session.get(Team, team.id)
        assert db_team is not None
        assert db_team.name == "Engineering Team"
```

### Using Test Factories

```python
@pytest.mark.integration
def test_team_with_members(self, integration_db_session: Session):
    """Test creating a team with members."""
    from app.test_factories import TeamFactory, UserFactory

    # Create test data using factories
    team = TeamFactory.create(integration_db_session)
    user1 = UserFactory.create(integration_db_session)
    user2 = UserFactory.create(integration_db_session)

    # Test your service logic
    service = TeamMemberService(integration_db_session)
    # ... rest of test
```

### Testing Complex Scenarios

```python
@pytest.mark.integration
def test_cascading_delete_team_cleans_up_all_data(
    self, integration_db_session: Session
):
    """Verify that deleting a team cascades to all related records."""
    # Setup: Create team with members and sources
    team = TeamFactory.create(integration_db_session)
    source = PrimaryAssetFactory.create(integration_db_session)

    service = TeamMemberService(integration_db_session)
    service.add_team_members(...)

    source_service = SourceAccessService(integration_db_session)
    source_service.add_team_sources(...)

    # Act: Delete the team
    team_service = TeamService(integration_db_session)
    team_service.delete_team(user=mock_user, team_id=team.id)

    # Assert: All related records are cleaned up
    assert integration_db_session.get(Team, team.id) is None
    # Verify cascade worked
    memberships = integration_db_session.exec(
        select(TeamMembership).where(TeamMembership.team_id == team.id)
    ).all()
    assert len(memberships) == 0
```

### Available Test Data

The fixtures automatically create these organizations:

```python
# Automatically available in all integration tests
organizations = [
    {"id": "test-org-id", "name": "Test Organization"},
    {"id": "org-1-id", "name": "Organization 1"},
    {"id": "org-2-id", "name": "Organization 2"},
]
```

---

## Running Tests

### Run All Integration Tests

```bash
# From backend directory
cd backend

# Run all integration tests
poetry run pytest -m integration

# With verbose output
poetry run pytest -m integration -v

# With detailed output and no capture (see print statements)
poetry run pytest -m integration -v -s
```

### Run Specific Tests

```bash
# Run tests in specific file
poetry run pytest app/services/test_team_service_integration.py -m integration

# Run specific test class
poetry run pytest app/services/test_team_service_integration.py::TestTeamLifecycleIntegration -m integration

# Run specific test method
poetry run pytest app/services/test_team_service_integration.py::TestTeamLifecycleIntegration::test_create_team -m integration

# Run tests matching pattern
poetry run pytest -m integration -k "team"
```

### Useful Flags

```bash
# Show test output even on success
poetry run pytest -m integration -v -s

# Stop on first failure
poetry run pytest -m integration -x

# Run last failed tests only
poetry run pytest -m integration --lf

# Show local variables on failure
poetry run pytest -m integration -l

# Generate coverage report
poetry run pytest -m integration --cov=app --cov-report=html
```

### Performance

Typical run times:
- **Single test:** 3-5 seconds (includes container startup)
- **Full suite (23 tests):** 40-45 seconds
- **Container startup:** ~2-3 seconds
- **Schema creation:** ~100ms

---

## Troubleshooting

### Docker Not Running

**Error:**
```
docker.errors.DockerException: Error while fetching server API version
```

**Solution:**
```bash
# Start Docker Desktop
# Or start Docker daemon
sudo systemctl start docker  # Linux
```

### Port Already in Use

**Error:**
```
Container startup failed: port 5432 already in use
```

**Solution:**
Testcontainers automatically uses random available ports. This error usually means:
1. Check if PostgreSQL is running locally: `lsof -i :5432`
2. Stop local PostgreSQL: `brew services stop postgresql` (macOS)
3. Or let Testcontainers handle it (it uses random ports anyway)

### Container Cleanup Issues

**Symptom:** Lots of stopped containers piling up

```bash
# Check for stopped containers
docker ps -a | grep postgres

# Clean up manually
docker container prune

# Or remove all testcontainers
docker ps -a | grep testcontainers | awk '{print $1}' | xargs docker rm
```

**Prevention:** Testcontainers should auto-cleanup, but if tests are interrupted (Ctrl+C), containers may remain.

### Slow Test Execution

**Issue:** Tests taking too long

**Optimization strategies:**

1. **Use `scope="session"` for stable data:**
   ```python
   # NOT recommended for our tests (we want isolation)
   # But useful if you have truly read-only tests
   @pytest.fixture(scope="session")
   def shared_db_engine():
       # Container lives for entire test session
       pass
   ```

2. **Parallel execution:**
   ```bash
   # Install pytest-xdist
   poetry add --group dev pytest-xdist

   # Run tests in parallel (4 workers)
   poetry run pytest -m integration -n 4
   ```

   ⚠️ **Note:** With `scope="function"`, each test gets its own container, so parallelization works great!

3. **Run subset of tests during development:**
   ```bash
   # Test only what you're working on
   poetry run pytest -m integration -k "test_create_team"
   ```

### Schema/Table Not Found

**Error:**
```
sqlalchemy.exc.ProgrammingError: relation "team" does not exist
```

**Causes:**
1. Missing table in `tables_to_create` list
2. Foreign key dependency ordering issue

**Solution:**
Check `conftest.py` and ensure all required tables are listed:

```python
tables_to_create = [
    Organization.__table__,
    User.__table__,
    OrgMembership.__table__,
    Team.__table__,           # Make sure this is here
    TeamMembership.__table__,
    # ... etc
]
```

### Enum Type Errors

**Error:**
```
psycopg2.errors.InvalidTextRepresentation: invalid input value for enum
```

**Solution:**
Make sure you're using correct enum values:

```python
# ❌ Wrong
role="admin"

# ✅ Correct
role="asset_admin"  # For asset roles
role="team_admin"   # For team roles
role="org_member"   # For org roles
```

See `database/models_enums.py` for valid enum values.

---

## Best Practices

### 1. Always Mark Integration Tests

```python
# ✅ Good
@pytest.mark.integration
def test_database_operation(self, integration_db_session: Session):
    pass

# ❌ Bad - test won't use Testcontainers
def test_database_operation(self, integration_db_session: Session):
    pass
```

### 2. Use Fixtures Appropriately

```python
# ✅ Good - use the session fixture
def test_create_user(self, integration_db_session: Session):
    user = UserFactory.create(integration_db_session)
    # Test uses the session

# ❌ Bad - creates its own session
def test_create_user(self, integration_db_engine: Engine):
    session = Session(integration_db_engine)  # Don't do this
    # Use the fixture instead!
```

### 3. Clean Test Data

```python
# ✅ Good - each test is independent
def test_team_count(self, integration_db_session: Session):
    # Create exactly what you need
    team1 = TeamFactory.create(integration_db_session)
    team2 = TeamFactory.create(integration_db_session)

    # Test with known data
    assert count_teams() == 2

# ❌ Bad - depends on other tests
def test_team_count(self, integration_db_session: Session):
    # Assumes teams already exist from other tests
    assert count_teams() > 0  # Fragile!
```

### 4. Test Real Scenarios

```python
# ✅ Good - tests actual database behavior
def test_cascade_delete(self, integration_db_session: Session):
    team = TeamFactory.create(integration_db_session)
    member = TeamMemberFactory.create(
        integration_db_session,
        team_id=team.id
    )

    # Delete team and verify cascade
    integration_db_session.delete(team)
    integration_db_session.commit()

    # Verify member was also deleted
    assert integration_db_session.get(TeamMember, member.id) is None

# ❌ Bad - uses mocks instead of real DB
def test_cascade_delete_mocked(self):
    mock_db = MagicMock()  # Don't do this for integration tests
    # Use real database with Testcontainers!
```

### 5. Descriptive Test Names

```python
# ✅ Good
def test_user_cannot_access_other_organization_teams(self, ...):
    """Test that organization isolation is enforced."""
    pass

# ❌ Bad
def test_teams(self, ...):
    """Test teams."""  # What about teams?
    pass
```

### 6. One Assertion Theme Per Test

```python
# ✅ Good
def test_create_team_saves_to_database(self, integration_db_session):
    """Verify team creation persists to database."""
    team = TeamFactory.create(integration_db_session)
    db_team = integration_db_session.get(Team, team.id)
    assert db_team is not None

def test_create_team_sets_organization_id(self, integration_db_session):
    """Verify team is associated with correct organization."""
    team = TeamFactory.create(integration_db_session, org_id="test-org")
    assert team.organization_id == "test-org"

# ❌ Bad - tests multiple things
def test_create_team(self, integration_db_session):
    """Test team creation."""
    team = TeamFactory.create(integration_db_session)
    assert team.id is not None
    assert team.name is not None
    assert team.organization_id is not None
    assert len(team.members) == 0
    # Too many assertions - hard to debug failures
```

---

## FAQ

### Q: Why use Testcontainers instead of an in-memory database?

**A:** In-memory databases (like SQLite) don't fully support PostgreSQL features:
- ❌ PostgreSQL-specific types (JSONB, UUID, Arrays)
- ❌ PostgreSQL functions and operators
- ❌ Exact same constraints and indexes
- ❌ Same transaction behavior

Testcontainers gives you a **real PostgreSQL instance**, ensuring tests match production.

### Q: Do I need to clean up containers manually?

**A:** No! Testcontainers automatically removes containers when:
1. The test completes (success or failure)
2. The Python process exits
3. The fixture scope ends

Exception: If you interrupt tests with Ctrl+C, some containers may remain. Use `docker container prune` to clean up.

### Q: Can I use the same container for multiple tests?

**A:** Yes, but we don't recommend it for our tests. Current setup uses `scope="function"` for maximum isolation:

```python
# Current: Fresh container per test (recommended)
@pytest.fixture(scope="function")  # New container each test
def integration_db_engine():
    ...

# Alternative: Shared container (faster but less isolated)
@pytest.fixture(scope="session")  # One container for all tests
def integration_db_engine():
    ...
```

### Q: How do I debug a failing test?

**1. Enable SQL logging:**
```python
# In conftest.py
engine = create_engine(db_url, echo=True)  # Shows all SQL
```

**2. Keep container running:**
```python
# In conftest.py, comment out cleanup
yield engine
# postgres.stop()  # Comment this to keep container

# Then connect to it:
# docker ps  # Find container ID
# docker exec -it <container_id> psql -U test -d test
```

**3. Use pytest debugging:**
```bash
# Drop into debugger on failure
poetry run pytest -m integration --pdb

# Show local variables on failure
poetry run pytest -m integration -l
```

### Q: Can I run tests without Docker?

**A:** No, Testcontainers requires Docker. However, you can:

1. **Use unit tests** (don't require database):
   ```bash
   poetry run pytest -m "not integration"
   ```

2. **Set up manual PostgreSQL** (not recommended):
   ```python
   # Would need to modify conftest.py
   # Not using Testcontainers
   ```

### Q: What if I need additional PostgreSQL extensions?

**A:** Modify the container image in `conftest.py`:

```python
# Option 1: Use a custom image
postgres = PostgresContainer("postgres:16-alpine").with_env(
    "POSTGRES_INITDB_ARGS", "-c shared_preload_libraries=pg_stat_statements"
)

# Option 2: Install extension after startup
postgres.start()
engine = create_engine(postgres.get_connection_url())
with engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
```

### Q: How do I test migrations with Testcontainers?

**A:** Currently blocked by Alembic multiple heads issue. Once resolved:

```python
from alembic import command
from alembic.config import Config

# In conftest.py
alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", db_url)
command.upgrade(alembic_cfg, "head")
```

See note in `conftest.py` about resolving Alembic heads.

### Q: Are Testcontainer tests slower than unit tests?

**A:** Yes, but the tradeoff is worth it:

| Test Type | Speed | Coverage | When to Use |
|-----------|-------|----------|-------------|
| **Unit** | ~10ms | Logic only | Business logic, pure functions |
| **Integration** | ~3-5s | Full stack | Database operations, services |
| **E2E** | ~10-30s | Everything | User flows, API endpoints |

**Strategy:** Use all three types appropriately.

---

## Additional Resources

- **Testcontainers Python Docs:** https://testcontainers-python.readthedocs.io/
- **PostgreSQL Module:** https://testcontainers-python.readthedocs.io/en/latest/postgres/README.html
- **Internal Docs:**
  - `backend/app/conftest.py` - Fixture definitions
  - `backend/app/test_factories.py` - Test data factories
  - `CLAUDE.md` - General development guidelines

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2025-01-06 | Complete rewrite using Testcontainers |
| 1.0.0 | 2024-12-XX | Initial documentation - manual schema approach |

---

**Questions?** Ask in #engineering or create an issue in the repo.

**Contributing?** Please update this doc when you modify the test setup!
