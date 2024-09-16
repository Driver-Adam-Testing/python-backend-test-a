import uuid

import pytest
from database.models_v1 import (
    Codebase,
    DerivedContent,
    DerivedContentType,
    Enum_Codebase_Status,
    Enum_Derived_Content_Status,
    Workspace,
)
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from shared.interfaces.search import SearchInput, SearchResult, SearchResults
from shared.pipelines.search import (
    hybrid_search,
    keyword_search,
    search_content,
    semantic_search,
)


@pytest.fixture(scope="session")
def mock_engine():
    # Create a test database
    test_db_url = "postgresql+psycopg://postgres:changethis@localhost:5432/postgres"
    engine = create_engine(test_db_url)

    # Ensure the test database exists
    with engine.connect() as connection:
        connection.execute("commit")
        result = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname='search_test'"
        )
        if not result.fetchone():
            connection.execute("CREATE DATABASE search_test")

    # Connect to the test database
    test_db_url = "postgresql+psycopg://postgres:changethis@localhost:5432/search_test"
    test_engine = create_engine(test_db_url)

    SQLModel.metadata.create_all(test_engine)

    yield test_engine

    # Drop all tables and dispose of the engine
    SQLModel.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture(scope="session")
def populate_mock_data(mock_engine):
    with Session(mock_engine) as session:
        # Populate the session with mock data
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Test Workspace",
            description="A workspace for testing",
            organization_id="org1",
        )
        codebase = Codebase(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            codebase_name="Test Codebase",
            description="A codebase for testing",
            status=Enum_Codebase_Status.processing_complete,
        )
        content_type = DerivedContentType(
            id=uuid.uuid4(), type_name="Test Content Type"
        )
        derived_content = DerivedContent(
            id=uuid.uuid4(),
            content_type_id=content_type.id,
            workspace_id=workspace.id,
            codebase_id=codebase.id,
            relative_path="test/path",
            content="Test content",
            content_name="Test Content Name",
            status=Enum_Derived_Content_Status.generation_complete,
        )
        session.add(workspace)
        session.add(codebase)
        session.add(content_type)
        session.add(derived_content)
        session.commit()


@pytest.fixture
def session(mock_engine, populate_mock_data):
    with Session(mock_engine) as session:
        yield session


@pytest.fixture
def search_input():
    return SearchInput(
        query="test query",
        algorithm="keyword",
        workspace_id=None,
        codebase_id=None,
        organization_id=None,
        content_type=None,
        relative_path=None,
        result_limit=10,
        token_limit=None,
    )


# TODO: Make these tests return values that prove that they're searching correctly.
# TODO: Currently I'm just testing the imports and intialization of search input. Not useful.


def test_search_content_keyword(session, search_input):
    search_input.algorithm = "keyword"
    results = search_content(session, search_input)
    assert isinstance(results, SearchResults)
    assert all(isinstance(result, SearchResult) for result in results.results)


def test_search_content_semantic(session, search_input):
    search_input.algorithm = "semantic"
    results = search_content(session, search_input)
    assert isinstance(results, SearchResults)
    assert all(isinstance(result, SearchResult) for result in results.results)


def test_search_content_hybrid(session, search_input):
    search_input.algorithm = "hybrid"
    results = search_content(session, search_input)
    assert isinstance(results, SearchResults)
    assert all(isinstance(result, SearchResult) for result in results.results)


def test_keyword_search(session, search_input):
    results = keyword_search(session, search_input)
    assert isinstance(results, SearchResults)
    assert all(isinstance(result, SearchResult) for result in results.results)


def test_semantic_search(session, search_input):
    results = semantic_search(session, search_input)
    assert isinstance(results, SearchResults)
    assert all(isinstance(result, SearchResult) for result in results.results)


def test_hybrid_search(session, search_input):
    results = hybrid_search(session, search_input)
    assert isinstance(results, SearchResults)
    assert all(isinstance(result, SearchResult) for result in results.results)
