# test_models.py

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, text

from .models_v2 import (
    ChunkRow,
    ContentRow,
    FullNodeView,
    NodeRow,
    PrimaryAssetRow,
    VersionRow,
)

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


def test_primary_asset_table(session: Session) -> None:
    """Test creation and retrieval of a PrimaryAssetRow record."""
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    retrieved_asset = (
        session.query(PrimaryAssetRow).filter_by(display_name="Test Asset").one()
    )
    assert retrieved_asset.organization_id == "org_123"


def test_version_table(session: Session) -> None:
    """Test creation and retrieval of a VersionRow record."""
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    version = VersionRow(primary_asset_id=asset.id, display_name="Version 1")
    session.add(version)
    session.commit()

    retrieved_version = (
        session.query(VersionRow).filter_by(display_name="Version 1").one()
    )
    assert retrieved_version.primary_asset_id == asset.id


def test_node_table(session: Session) -> None:
    """Test creation and retrieval of a NodeRow record."""
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    version = VersionRow(primary_asset_id=asset.id, display_name="Version 1")
    session.add(version)
    session.commit()

    node = NodeRow(version_id=version.id, relative_path="/path/to/node")
    session.add(node)
    session.commit()

    retrieved_node = (
        session.query(NodeRow).filter_by(relative_path="/path/to/node").one()
    )
    assert retrieved_node.version_id == version.id


def test_content_table(session: Session) -> None:
    """Test creation and retrieval of a ContentRow record."""
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    version = VersionRow(primary_asset_id=asset.id, display_name="Version 1")
    session.add(version)
    session.commit()

    node = NodeRow(version_id=version.id, relative_path="/path/to/node")
    session.add(node)
    session.commit()

    content = ContentRow(
        version_node_id=node.id, text="Sample content", content_type="text/plain"
    )
    session.add(content)
    session.commit()

    retrieved_content = session.query(ContentRow).filter_by(text="Sample content").one()
    assert retrieved_content.version_node_id == node.id


def test_chunk_table(session: Session) -> None:
    """Test creation and retrieval of a ChunkRow record."""
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    version = VersionRow(primary_asset_id=asset.id, display_name="Version 1")
    session.add(version)
    session.commit()

    node = NodeRow(version_id=version.id, relative_path="/path/to/node")
    session.add(node)
    session.commit()

    content = ContentRow(
        version_node_id=node.id, text="Sample content", content_type="text/plain"
    )
    session.add(content)
    session.commit()

    chunk = ChunkRow(
        content_id=content.id,
        text="Chunk text",
        chunk_number=1,
        text_embedding_3_small=[0.1] * 1536,  # Sample embedding vector
    )
    session.add(chunk)
    session.commit()

    retrieved_chunk = session.query(ChunkRow).filter_by(chunk_number=1).one()
    assert retrieved_chunk.content_id == content.id


def test_save_functionality(session: Session) -> None:
    """Test the save functionality of FullNodeView."""
    # Create and commit a primary asset
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    # Create and commit a version linked to the primary asset
    version = VersionRow(primary_asset_id=asset.id, display_name="Version 1")
    session.add(version)
    session.commit()

    # Create and commit a node linked to the version
    node = NodeRow(version_id=version.id, relative_path="/path/to/node")
    session.add(node)
    session.commit()

    # Create a FullNodeView instance and save it
    full_node_view = FullNodeView(
        primary_asset_id=asset.id,
        primary_asset_display_name=asset.display_name,
        primary_asset_organization_id=asset.organization_id,
        version_id=version.id,
        version_display_name=version.display_name,
        node_id=node.id,
        node_relative_path=node.relative_path,
    )
    full_node_view.add(session)
    session.commit()  # Ensure changes are committed

    # Retrieve and assert the saved data
    retrieved_asset = session.query(PrimaryAssetRow).filter_by(id=asset.id).one()
    assert retrieved_asset.display_name == "Test Asset"
    assert retrieved_asset.organization_id == "org_123"

    retrieved_version = session.query(VersionRow).filter_by(id=version.id).one()
    assert retrieved_version.display_name == "Version 1"

    retrieved_node = session.query(NodeRow).filter_by(id=node.id).one()
    assert retrieved_node.relative_path == "/path/to/node"


def test_query_full_nodes(session: Session) -> None:
    """Test querying the FullNodeView for expected data."""
    # Create and commit a primary asset
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    # Create and commit a version linked to the primary asset
    version = VersionRow(primary_asset_id=asset.id, display_name="Version 1")
    session.add(version)
    session.commit()

    # Create and commit a node linked to the version
    node = NodeRow(version_id=version.id, relative_path="/path/to/node")
    session.add(node)
    session.commit()

    # Create a FullNodeView instance and save it
    full_node_view = FullNodeView(
        primary_asset_id=asset.id,
        primary_asset_display_name=asset.display_name,
        primary_asset_organization_id=asset.organization_id,
        version_id=version.id,
        version_display_name=version.display_name,
        node_id=node.id,
        node_relative_path=node.relative_path,
    )
    full_node_view.add(session)
    session.commit()  # Ensure changes are committed

    # Query the FullNodeView
    retrieved_full_node = session.query(FullNodeView).filter_by(node_id=node.id).one()

    # Assert the retrieved data matches the expected values
    assert retrieved_full_node.primary_asset_id == asset.id
    assert retrieved_full_node.primary_asset_display_name == "Test Asset"
    assert retrieved_full_node.primary_asset_organization_id == "org_123"
    assert retrieved_full_node.version_id == version.id
    assert retrieved_full_node.version_display_name == "Version 1"
    assert retrieved_full_node.node_id == node.id
    assert retrieved_full_node.node_relative_path == "/path/to/node"


def test_relationships_populated(session: Session) -> None:
    """Test that all relationship fields are populated correctly."""
    # Create and commit a primary asset
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    # Create and commit a version linked to the primary asset
    version = VersionRow(primary_asset_id=asset.id, display_name="Version 1")
    session.add(version)
    session.commit()

    # Create and commit a node linked to the version
    node = NodeRow(version_id=version.id, relative_path="/path/to/node")
    session.add(node)
    session.commit()

    # Create and commit content linked to the node
    content = ContentRow(
        version_node_id=node.id, text="Sample content", content_type="text/plain"
    )
    session.add(content)
    session.commit()

    # Create and commit a chunk linked to the content
    chunk = ChunkRow(
        content_id=content.id,
        text="Chunk text",
        chunk_number=1,
        text_embedding_3_small=[0.1] * 1536,  # Sample embedding vector
    )
    session.add(chunk)
    session.commit()

    # Retrieve and assert relationships
    retrieved_version = session.query(VersionRow).filter_by(id=version.id).one()
    assert retrieved_version.primary_asset.id == asset.id

    retrieved_node = session.query(NodeRow).filter_by(id=node.id).one()
    assert retrieved_node.version.id == version.id

    retrieved_content = session.query(ContentRow).filter_by(id=content.id).one()
    assert retrieved_content.node.id == node.id

    retrieved_chunk = session.query(ChunkRow).filter_by(id=chunk.id).one()
    assert retrieved_chunk.content.id == content.id


def test_cascading_deletes(session: Session) -> None:
    """Test that cascading deletes work correctly."""

    # Create and commit a primary asset
    asset = PrimaryAssetRow(display_name="Test Asset", organization_id="org_123")
    session.add(asset)
    session.commit()

    # Create and commit a version linked to the primary asset
    version = VersionRow(primary_asset_id=asset.id, display_name="Version 1")
    session.add(version)
    session.commit()

    # Save the version id
    version_id = version.id

    # Create and commit a node linked to the version
    node = NodeRow(version_id=version.id, relative_path="/path/to/node")
    session.add(node)
    session.commit()

    # Save the node id
    node_id = node.id

    # Create and commit content linked to the node
    content = ContentRow(
        version_node_id=node.id, text="Sample content", content_type="text/plain"
    )
    session.add(content)
    session.commit()

    # Save the content id
    content_id = content.id

    # Create and commit a chunk linked to the content
    chunk = ChunkRow(
        content_id=content.id,
        text="Chunk text",
        chunk_number=1,
        text_embedding_3_small=[0.1] * 1536,  # Sample embedding vector
    )
    session.add(chunk)
    session.commit()

    # Save the chunk id
    chunk_id = chunk.id

    session.refresh(asset)
    session.execute(
        text("DELETE FROM v2_primary_asset WHERE id = :id"), {"id": asset.id}
    )
    session.commit()

    # Assert that the version, node, content, and chunk are deleted
    assert session.query(VersionRow).filter_by(id=version_id).one_or_none() is None
    assert session.query(NodeRow).filter_by(id=node_id).one_or_none() is None
    assert session.query(ContentRow).filter_by(id=content_id).one_or_none() is None
    assert session.query(ChunkRow).filter_by(id=chunk_id).one_or_none() is None
