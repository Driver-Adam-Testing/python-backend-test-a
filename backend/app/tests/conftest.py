from collections.abc import Generator
from unittest.mock import Mock

import pytest
from database.db import engine, init_db
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import initial_data
from app.api.auth import CurrentUser
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        initial_data.init(session)
        yield session


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def current_user_with_org() -> CurrentUser:
    current_user = Mock(spec=CurrentUser)
    current_user.user_id = "testuserid"
    current_user.organization_id = "testorgid"
    current_user.is_service_account = False
    return current_user


@pytest.fixture(scope="module")
def current_user_without_org() -> CurrentUser:
    current_user = Mock(spec=CurrentUser)
    current_user.user_id = "testuserid"
    current_user.organization_id = None
    current_user.is_service_account = False
    return current_user


@pytest.fixture(scope="module")
def current_user_without_id() -> CurrentUser:
    current_user = Mock(spec=CurrentUser)
    current_user.user_id = None
    current_user.organization_id = "testorgid"
    current_user.is_service_account = False
    return current_user
