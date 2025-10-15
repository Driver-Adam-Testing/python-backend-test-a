"""Test version using real Auth0 event processor with mocked database operations."""

import logging
from typing import Any
from unittest.mock import MagicMock, patch

from .auth0_event_schema import (
    Auth0EventProcessingResult,
)

logger = logging.getLogger(__name__)

# Global mock state to track database operations
MOCK_DB_STATE = {
    "users": {},
    "organizations": {},
    "memberships": set(),
    "operations": [],
}


def clear_test_state() -> None:
    MOCK_DB_STATE["users"].clear()
    MOCK_DB_STATE["organizations"].clear()
    MOCK_DB_STATE["memberships"].clear()
    MOCK_DB_STATE["operations"].clear()


def get_test_state() -> dict[str, Any]:
    return {
        "users": dict(MOCK_DB_STATE["users"]),
        "organizations": dict(MOCK_DB_STATE["organizations"]),
        "memberships": list(MOCK_DB_STATE["memberships"]),
        "operations": list(MOCK_DB_STATE["operations"]),
    }


class MockUser:
    def __init__(self, user_data: dict | None = None):
        if user_data:
            self.id = user_data["id"]
            self.email = user_data["email"]
            self.name = user_data["name"]
            self.auth0_updated_at = user_data["auth0_updated_at"]
        else:
            self.id = None
            self.email = None
            self.name = None
            self.auth0_updated_at = None


class MockOrganization:
    def __init__(self, org_data: dict | None = None):
        if org_data:
            self.id = org_data["id"]
            self.name = org_data["name"]
            self.display_name = org_data.get("display_name")
            self.org_metadata = org_data.get("org_metadata", {})
            self.auth0_updated_at = org_data["auth0_updated_at"]
        else:
            self.id = None


class MockOrgMembership:
    def __init__(self, user_id: str, org_id: str):
        self.user_id = user_id
        self.org_id = org_id
        self.id = f"{user_id}:{org_id}"


class MockQueryResult:
    def __init__(self, results: list = None):
        self._results = results or []

    def first(self):
        return self._results[0] if self._results else None

    def all(self):
        return self._results


class MockSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def get(self, model_class, entity_id):
        # Mock User model lookup
        if (
            hasattr(model_class, "__tablename__")
            and model_class.__tablename__ == "user"
        ):
            user_data = MOCK_DB_STATE["users"].get(entity_id)
            return MockUser(user_data) if user_data else None
        # Mock Organization model lookup
        elif (
            hasattr(model_class, "__tablename__")
            and model_class.__tablename__ == "organization"
        ):
            org_data = MOCK_DB_STATE["organizations"].get(entity_id)
            return MockOrganization(org_data) if org_data else None
        return None

    def add(self, obj):
        if hasattr(obj, "id") and hasattr(obj, "email"):  # User
            user_data = {
                "id": obj.id,
                "email": obj.email,
                "name": obj.name,
                "auth0_updated_at": obj.auth0_updated_at,
            }
            MOCK_DB_STATE["users"][obj.id] = user_data
            MOCK_DB_STATE["operations"].append(
                {"action": "INSERT", "table": "user", "data": user_data}
            )
            logger.info(f"[TEST] Would INSERT user: {obj.email} ({obj.id})")

        elif (
            hasattr(obj, "id") and hasattr(obj, "name") and not hasattr(obj, "user_id")
        ):  # Organization
            org_data = {
                "id": obj.id,
                "name": obj.name,
                "display_name": obj.display_name,
                "org_metadata": obj.org_metadata,
                "auth0_updated_at": obj.auth0_updated_at,
            }
            MOCK_DB_STATE["organizations"][obj.id] = org_data
            MOCK_DB_STATE["operations"].append(
                {"action": "INSERT", "table": "organization", "data": org_data}
            )
            logger.info(f"[TEST] Would INSERT organization: {obj.name} ({obj.id})")

        elif hasattr(obj, "user_id") and hasattr(obj, "org_id"):  # Membership
            MOCK_DB_STATE["memberships"].add((obj.user_id, obj.org_id))
            MOCK_DB_STATE["operations"].append(
                {
                    "action": "INSERT",
                    "table": "org_membership",
                    "data": {"user_id": obj.user_id, "org_id": obj.org_id},
                }
            )
            logger.info(
                f"[TEST] Would INSERT membership: {obj.user_id} -> {obj.org_id}"
            )

    def delete(self, obj):
        if hasattr(obj, "id") and hasattr(obj, "email"):  # User
            MOCK_DB_STATE["users"].pop(obj.id, None)
            MOCK_DB_STATE["memberships"] = {
                (u, o) for (u, o) in MOCK_DB_STATE["memberships"] if u != obj.id
            }
            MOCK_DB_STATE["operations"].append(
                {"action": "DELETE", "table": "user", "data": {"id": obj.id}}
            )
            logger.info(f"[TEST] Would DELETE user: {obj.id}")

        elif hasattr(obj, "user_id") and hasattr(obj, "org_id"):  # Membership
            MOCK_DB_STATE["memberships"].discard((obj.user_id, obj.org_id))
            MOCK_DB_STATE["operations"].append(
                {
                    "action": "DELETE",
                    "table": "org_membership",
                    "data": {"user_id": obj.user_id, "org_id": obj.org_id},
                }
            )
            logger.info(
                f"[TEST] Would DELETE membership: {obj.user_id} -> {obj.org_id}"
            )

    def exec(self, query):
        if "OrgMembership" in str(query):
            return MockQueryResult([])
        return MockQueryResult([])

    def commit(self):
        self.committed = True
        logger.debug("[TEST] Would COMMIT transaction")
        MOCK_DB_STATE["operations"].append(
            {"action": "COMMIT", "table": None, "data": None}
        )

    def rollback(self):
        self.rolled_back = True
        logger.debug("[TEST] Would ROLLBACK transaction")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def process_auth0_event_test(event_dict: dict[str, Any]) -> Auth0EventProcessingResult:
    """Test version using real Auth0 event processor with mocked database operations."""
    # Import the module first so patch can find it
    from src.event_processor import auth0_event_processor

    # Create better mocks that work with SQLAlchemy
    class MockUserModel:
        __tablename__ = "user"

        def __init__(self, id=None, email=None, name=None, auth0_updated_at=None):
            self.id = id
            self.email = email
            self.name = name
            self.auth0_updated_at = auth0_updated_at

    class MockOrganizationModel:
        __tablename__ = "organization"

        def __init__(
            self,
            id=None,
            name=None,
            display_name=None,
            org_metadata=None,
            auth0_updated_at=None,
        ):
            self.id = id
            self.name = name
            self.display_name = display_name
            self.org_metadata = org_metadata or {}
            self.auth0_updated_at = auth0_updated_at

    class MockOrgMembershipModel:
        __tablename__ = "org_membership"
        user_id = MagicMock()  # Column attribute for SQLAlchemy queries
        org_id = MagicMock()  # Column attribute for SQLAlchemy queries

        def __init__(self, user_id=None, org_id=None):
            self.user_id = user_id
            self.org_id = org_id

    # Create a mock session factory that returns our MockSession
    def mock_session_factory(*args, **kwargs):
        return MockSession()

    # Patch the database engine and models, then call the real processor
    with (
        patch.object(auth0_event_processor, "engine") as mock_engine,
        patch.object(auth0_event_processor, "Session", mock_session_factory),
        patch.object(auth0_event_processor, "User", MockUserModel),
        patch.object(auth0_event_processor, "Organization", MockOrganizationModel),
        patch.object(auth0_event_processor, "OrgMembership", MockOrgMembershipModel),
        patch.object(auth0_event_processor, "select") as mock_select,
    ):
        # Mock the select function to return a query object that our MockSession can handle
        mock_select.return_value = MagicMock()

        return auth0_event_processor.process_auth0_event(event_dict)


def test_event_with_logging(event_dict: dict[str, Any]) -> dict[str, Any]:
    # Clear previous test state
    clear_test_state()

    # Process the event using real processor with mocked DB
    result = process_auth0_event_test(event_dict)

    # Get the final state and operations
    test_state = get_test_state()

    test_result = {
        "processing_result": result.model_dump(),
        "database_operations": test_state["operations"],
        "final_mock_state": {
            "users": test_state["users"],
            "organizations": test_state["organizations"],
            "memberships": test_state["memberships"],
        },
        "success": result.processed,
        "summary": {
            "operations_count": len(test_state["operations"]),
            "entities_updated": result.entities_updated,
            "users_affected": len(test_state["users"]),
            "memberships_affected": len(test_state["memberships"]),
        },
    }

    return test_result
