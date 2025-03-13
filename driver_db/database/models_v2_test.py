# test_models.py

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session

# Define the test database URL (adjust with your credentials)
TEST_DATABASE_URL = "postgresql://postgres:changethis@localhost:5432/postgres"


@pytest.fixture(scope="session")
def engine() -> create_engine:
    """Create a test database, run migrations, and yield an engine connected to it."""
    # Ensure the test database is fresh

    engine = create_engine(TEST_DATABASE_URL)

    yield engine

    # Cleanup after tests
    engine.dispose()


@pytest.fixture(scope="session")
def connection(engine: create_engine) -> None:
    """Establish a connection to the test database."""
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture(scope="function")
def session(engine: create_engine) -> Session:
    """Provide a transactional scope around a series of operations."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def test_session_creation(session: Session) -> None:
    assert session is not None
