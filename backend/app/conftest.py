from unittest.mock import Mock

import pytest

from app.api.auth import UserToken

# TODO: disabled for now until we have a better local test with db in the loop solution
# that can't screw us over by using a real db instance

# @pytest.fixture(scope="function", autouse=True)
# def db() -> Generator[Session, None, None]:
#     # commenting out the drop_all and create_all calls to avoid dropping the tables in deployed environments
#     # SQLModel.metadata.create_all(engine)
#     with Session(engine) as session:
#         yield session
#     # SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def current_user_with_org() -> UserToken:
    current_user = Mock(spec=UserToken)
    current_user.user_id = "test_user_id"
    current_user.organization_id = "test_org_id"
    current_user.organization_name = "test_org_name"
    current_user.is_service_account = False
    return current_user


@pytest.fixture(scope="function")
def current_user_with_other_org() -> UserToken:
    current_user = Mock(spec=UserToken)
    current_user.user_id = "other_test_user_id"
    current_user.organization_id = "other_test_org_id"
    current_user.organization_name = "other_test_org_name"
    current_user.is_service_account = False
    return current_user
