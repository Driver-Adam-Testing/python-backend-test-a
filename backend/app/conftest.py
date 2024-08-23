import pytest
from collections.abc import Generator
from unittest.mock import Mock

from database.db import engine
from sqlmodel import Session, SQLModel
from app.api.auth import CurrentUser

@pytest.fixture(scope="function", autouse=True)
def db() -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def current_user_with_org() -> CurrentUser:
    current_user = Mock(spec=CurrentUser)
    current_user.user_id = "test_user_id"
    current_user.organization_id = "test_org_id"
    current_user.is_service_account = False
    return current_user
