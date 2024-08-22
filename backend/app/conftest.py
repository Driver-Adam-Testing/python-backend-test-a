from collections.abc import Generator

import pytest
from database.db import engine
from sqlmodel import Session, SQLModel


@pytest.fixture(scope="function", autouse=True)
def db() -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)
