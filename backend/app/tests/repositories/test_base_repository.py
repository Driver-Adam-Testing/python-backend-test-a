from unittest.mock import MagicMock
from uuid import UUID

import pytest
from sqlmodel import Field, SQLModel

from app.repositories.base_repository import BaseRepository


# Define a mock model for testing
class MockModel(SQLModel, table=True):
    id: UUID | None = Field(default=None, primary_key=True)
    name: str


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def base_repository(session):
    return BaseRepository(session, MockModel)


def test_get(base_repository, session):
    mock_instance = MockModel(
        id=UUID("12345678-1234-5678-1234-567812345678"), name="Test"
    )
    session.get.return_value = mock_instance

    result = base_repository.get(UUID("12345678-1234-5678-1234-567812345678"))

    session.get.assert_called_once_with(
        MockModel, UUID("12345678-1234-5678-1234-567812345678")
    )
    assert result == mock_instance


def test_get_all(base_repository, session):
    mock_instances = [
        MockModel(id=UUID("12345678-1234-5678-1234-567812345678"), name="Test1"),
        MockModel(id=UUID("87654321-4321-8765-4321-876543218765"), name="Test2"),
    ]
    session.exec.return_value.all.return_value = mock_instances

    result = base_repository.get_all()

    session.exec.assert_called_once()
    assert result == mock_instances


def test_create(base_repository, session):
    mock_instance = MockModel(name="Test")
    session.add.return_value = None
    session.commit.return_value = None
    session.refresh.return_value = None

    result = base_repository.create(mock_instance)

    session.add.assert_called_once_with(mock_instance)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(mock_instance)
    assert result == mock_instance


def test_update(base_repository, session):
    mock_instance = MockModel(
        id=UUID("12345678-1234-5678-1234-567812345678"), name="Test"
    )
    update_data = {"name": "Updated Test"}
    session.commit.return_value = None
    session.refresh.return_value = None

    result = base_repository.update(mock_instance, update_data)

    assert mock_instance.name == "Updated Test"
    session.add.assert_called_once_with(mock_instance)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(mock_instance)
    assert result == mock_instance


def test_delete(base_repository, session):
    mock_instance = MockModel(
        id=UUID("12345678-1234-5678-1234-567812345678"), name="Test"
    )
    session.get.return_value = mock_instance
    session.delete.return_value = None
    session.commit.return_value = None

    result = base_repository.delete(UUID("12345678-1234-5678-1234-567812345678"))

    session.get.assert_called_once_with(
        MockModel, UUID("12345678-1234-5678-1234-567812345678")
    )
    session.delete.assert_called_once_with(mock_instance)
    session.commit.assert_called_once()
    assert result == mock_instance


def test_delete_not_found(base_repository, session):
    session.get.return_value = None

    result = base_repository.delete(UUID("12345678-1234-5678-1234-567812345678"))

    session.get.assert_called_once_with(
        MockModel, UUID("12345678-1234-5678-1234-567812345678")
    )
    session.delete.assert_not_called()
    session.commit.assert_not_called()
    assert result is None
