from uuid import uuid4

import pytest
import sqlalchemy
from sqlmodel import SQLModel

from .db import get_session
from .models_v2 import (
    Chunk,
    Content,
    ContentCategoryEnum,
    ContentTypeEnum,
    Node,
    NodeDto,
    Tag,
)


@pytest.fixture(scope="module", autouse=True)
def setup_database() -> None:
    # Create tables in the PostgreSQL database
    with get_session() as session:
        SQLModel.metadata.create_all(bind=session.bind)


@pytest.fixture
def db_session() -> sqlalchemy.orm.Session:
    with get_session() as session:
        yield session


def test_node_creation(db_session: sqlalchemy.orm.Session) -> None:
    node = Node(
        path="test/path", organization_id="org123", custom_display_name="Test Node"
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)

    assert node.id is not None
    assert node.path == "test/path"
    assert node.organization_id == "org123"
    assert node.display_name == "Test Node"


def test_node_dto_conversion() -> None:
    node = Node(
        path="test/path", organization_id="org123", custom_display_name="Test Node"
    )
    node_dto = NodeDto.from_node(node)
    assert node_dto.path == node.path
    assert node_dto.organization_id == node.organization_id

    node_converted = node_dto.to_node()
    assert node_converted.path == node.path
    assert node_converted.organization_id == node.organization_id


def test_content_validation(db_session: sqlalchemy.orm.Session) -> None:
    content = Content(
        node_id=uuid4(),
        content_type=ContentTypeEnum.LONG_SUMMARY.value,
        category=ContentCategoryEnum.SYSTEM_GENERATED.value,
        content="Sample content",
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    assert content.id is not None
    assert content.content_type == ContentTypeEnum.LONG_SUMMARY.value
    assert content.category == ContentCategoryEnum.SYSTEM_GENERATED.value

    # Test invalid content type
    with pytest.raises(ValueError):
        invalid_content = Content(
            node_id=uuid4(),
            content_type="INVALID_TYPE",
            category=ContentCategoryEnum.SYSTEM_GENERATED.value,
            content="Invalid content",
        )
        db_session.add(invalid_content)
        db_session.commit()

    # Test invalid category
    with pytest.raises(ValueError):
        invalid_content = Content(
            node_id=uuid4(),
            content_type=ContentTypeEnum.LONG_SUMMARY.value,
            category="INVALID_CATEGORY",
            content="Invalid content",
        )
        db_session.add(invalid_content)
        db_session.commit()


def test_chunk_creation(db_session: sqlalchemy.orm.Session) -> None:
    content = Content(
        node_id=uuid4(),
        content_type=ContentTypeEnum.LONG_SUMMARY.value,
        category=ContentCategoryEnum.SYSTEM_GENERATED.value,
        content="Sample content",
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    chunk = Chunk(content_id=content.id, text="Sample chunk text", chunk_number=1)
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)

    assert chunk.id is not None
    assert chunk.text == "Sample chunk text"
    assert chunk.chunk_number == 1


def test_tag_creation(db_session: sqlalchemy.orm.Session) -> None:
    tag = Tag(name="Sample Tag", hex_color="#FFFFFF", organization_id=uuid4())
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)

    assert tag.id is not None
    assert tag.name == "Sample Tag"
    assert tag.hex_color == "#FFFFFF"

    # Test unique constraint on tag name and organization_id
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        duplicate_tag = Tag(
            name="Sample Tag", hex_color="#000000", organization_id=tag.organization_id
        )
        db_session.add(duplicate_tag)
        db_session.commit()
