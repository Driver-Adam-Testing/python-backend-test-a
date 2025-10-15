"""
Auth0 Event Processor - Eventual Consistency Architecture

It follows an "events are signals" approach where events trigger us to fetch the
current state from Auth0 and write it to our DB.

DESIGN PRINCIPLES:
------------------
1. Events are signals, not state
   - Events tell us "something changed", not "what the new state is"
   - We always fetch fresh data from Auth0 when processing events
   - Auth0 is the source of truth

2. Eventual consistency
   - Events can arrive out of order (membership before user creation)
   - Events can be delayed (state changes between event and processing)
   - We handle this with backfills and timestamp guards
   - Reconciliation job must run regularly to catch divergence

3. Fail-fast for infrastructure issues
   - Auth0 auth failures bubble to Lambda (config issue, needs alerts)
   - DB failures bubble to Lambda (retry, then DLQ)
   - Missing required fields raise immediately (API contract violation)

4. Graceful handling of race conditions
   - 404s during processing are expected (deletion races)
   - Timestamp guards prevent overwriting newer data with older data
   - We log and skip rather than fail on expected races

KNOWN LIMITATIONS:
------------------
1. NO IDEMPOTENCY TRACKING
   - We extract log_id but don't check if event was already processed
   - Lambda timeouts after successful DB commit will cause duplicate processing
   - Duplicate processing is mostly safe (upserts) but not ideal
   - TODO: Add ProcessedEvent table to track log_id and prevent duplicate processing

2. TOCTOU (Time-of-Check-Time-of-Use) gaps
   - We fetch from Auth0, then commit to DB seconds later
   - Auth0 state can change in this window
   - We write state that may be stale by commit time
   - This is acceptable with reconciliation but can cause brief inconsistency

3. Lost events cause permanent divergence
   - If an event goes to DLQ and is never replayed, DB diverges from Auth0
   - CRITICAL: Reconciliation is not optional, it's required for correctness
   - Reconciliation must run frequently (nightly minimum, hourly recommended)

4. No transaction isolation across Auth0 and DB
   - We can't atomically check Auth0 and update DB
   - Multi-step operations (fetch user, fetch org, create membership) are not atomic
   - Race conditions possible but reconciliation fixes them

FUTURE IMPROVEMENTS:
--------------------
1. Add idempotency tracking with ProcessedEvent table
2. Add metrics/monitoring for event processing lag
3. Consider adding event replay capability for DLQ events
4. Add alerting when events consistently fail (not just transient 404s)
5. Consider batching reconciliation triggers on repeated failures

RECONCILIATION REQUIREMENTS:
---------------------------
This event processor is NOT sufficient alone. It requires a reconciliation job that:
- Runs regularly (nightly minimum, hourly recommended)
- Fetches all users/orgs/memberships from Auth0
- Compares with DB state
- Corrects any divergence
- Alerts on large divergences (indicates event processing issues)
"""

import logging
from datetime import UTC, datetime
from typing import Any

import requests
from database.db import engine
from database.models import Organization, OrgMembership, User
# from shared.auth0.auth0_retry import retry_auth0_call
from shared.auth0.auth0_service import Auth0Service
from sqlmodel import Session, select

from .auth0_event_schema import (
    Auth0EventBridgeEvent,
    Auth0EventProcessingResult,
    extract_log_id,
)
from config import settings

logger = logging.getLogger(__name__)

# Module-level Auth0Service instance (created once on import)
auth0_service = Auth0Service(
    auth0_mgmt_domain=settings.AUTH0_MGMT_API_DOMAIN,
    auth0_mgmt_client_id=settings.AUTH0_MGMT_API_CLIENT_ID,
    auth0_mgmt_client_secret=settings.AUTH0_MGMT_API_CLIENT_SECRET,
    auth0_domain=settings.AUTH0_DOMAIN,
    auth0_client_id=settings.AUTH0_CLIENT_ID,
)


def normalize_auth0_user_id(user_id: str | None) -> str | None:
    """
    Normalize Auth0 user ID to ensure it has the proper prefix.

    Auth0 events sometimes contain user IDs without the provider prefix
    (e.g., "68e58290f57d065d26ae5301" instead of "auth0|68e58290f57d065d26ae5301").
    The Auth0 Management API requires the full format.

    Returns:
        Normalized user ID with proper prefix, or None if input is None/empty
    """
    if not user_id:
        return None

    # If it already has a provider prefix (contains |), return as-is
    if "|" in user_id:
        return user_id

    # If it looks like a standard Auth0 user ID (alphanumeric), prepend auth0|
    if user_id.replace("_", "").isalnum():
        return f"auth0|{user_id}"

    # For other formats, return as-is and let Auth0 API handle it
    return user_id


def process_auth0_event(event_dict: dict[str, Any]) -> Auth0EventProcessingResult:
    """Process a single Auth0 event. Events are signals - always fetch fresh data from Auth0.

    Raises:
        Any exception will bubble to Lambda runtime, causing retry or DLQ.
    """
    event = Auth0EventBridgeEvent.model_validate(event_dict)
    log_id = extract_log_id(event)
    event_type = event.detail.data.type

    logger.info(f"Processing Auth0 event: {event_type} (log_id: {log_id})")

    entities_updated = []

    if event_type in {"s", "ss"}:
        entities_updated.extend(_handle_user_event(event))
    elif event_type == "sdu":
        entities_updated.extend(_handle_user_delete_event(event))
    elif "organization_member" in event_type:
        entities_updated.extend(_handle_membership_event(event))
    elif event_type == "sapi":
        entities_updated.extend(_handle_api_event(event))
    else:
        logger.info(f"Ignoring event type: {event_type}")

    return Auth0EventProcessingResult(
        log_id=log_id,
        event_type=event_type,
        processed=True,
        entities_updated=entities_updated,
    )


def _handle_user_event(event: Auth0EventBridgeEvent) -> list[str]:
    """Handle user create/update events (s, ss)"""
    user_id = normalize_auth0_user_id(event.detail.data.user_id)
    if not user_id:
        logger.warning("User event missing user_id")
        return []

    return _process_user_update(user_id)


def _process_user_update(user_id: str) -> list[str]:
    print(f"Processing user update: {user_id}")
    """Process a user update by fetching fresh data from Auth0."""
    try:
        # user_data = retry_auth0_call(lambda: auth0_service.get_user_profile(user_id))
        user_data = auth0_service.get_user_profile(user_id)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            # 404 is expected when user was deleted between event emission and processing.
            # EventBridge has eventual consistency - we get "user updated" event, but by the
            # time we process it, user may already be deleted in Auth0. This is a legitimate
            # race condition, not an error. We log and skip since the user no longer exists
            # in the source of truth (Auth0). Nightly reconciliation will clean up any
            # orphaned records in our DB.
            logger.info(
                f"User {user_id} not found in Auth0 (deleted between event and processing), skipping"
            )
            return []
        raise

    with Session(engine) as session:
        _upsert_user(session, user_data)
        session.commit()

    logger.info(f"Updated user: {user_id}")
    return ["user"]


def _handle_user_delete_event(event: Auth0EventBridgeEvent) -> list[str]:
    # user_id = normalize_auth0_user_id(event.detail.data.user_id)
    user_id = normalize_auth0_user_id(event.detail.data.details.get("request", {}).get("body", {}).get("members", [None])[0])
    if not user_id:
        logger.warning("User delete event missing user_id")
        return []

    with Session(engine) as session:
        user = session.get(User, user_id)
        memberships = session.exec(
            select(OrgMembership).where(OrgMembership.user_id == user_id)
        ).all()

        for membership in memberships:
            session.delete(membership)

        if user:
            session.delete(user)

        session.commit()

    logger.info(f"Deleted user and memberships: {user_id}")
    return ["user", "membership"]


def _handle_membership_event(event: Auth0EventBridgeEvent) -> list[str]:
    user_id = normalize_auth0_user_id(event.detail.data.user_id)
    org_id = event.detail.data.organization_id

    if not user_id or not org_id:
        logger.warning("Membership event missing user_id or org_id")
        return []

    return _process_membership_change(user_id, org_id)


def _process_membership_change(user_id: str, org_id: str) -> list[str]:
    """Process a membership change for the given user and organization.

    This function handles the complexity of eventual consistency:
    - Events can arrive out of order (membership event before user creation)
    - Auth0 state can change between fetch and DB commit (TOCTOU gap)
    - Entities may be deleted in Auth0 between event emission and processing

    Strategy:
    1. Fetch current membership state from Auth0 (source of truth)
    2. Backfill missing entities (user/org) if they should exist
    3. Update DB to match Auth0's current state
    4. Rely on reconciliation to fix any races or missed events

    Known limitation: The fetch from Auth0 (step 1) and DB commit (step 3) are
    not atomic. Auth0 state can change in between. This is acceptable because:
    - Subsequent events will correct the state
    - Reconciliation catches any divergence
    - Brief inconsistency is acceptable in eventual consistency model
    """
    try:
        # user_orgs = retry_auth0_call(
        #     lambda: auth0_service.get_user_organizations(user_id)
        # )
        user_orgs = auth0_service.get_user_organizations(user_id)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            # 404 is expected when user was deleted between event emission and processing.
            # Membership events can arrive out of order or be delayed. By the time we process
            # a membership change event, the user may have been deleted from Auth0. This is
            # a legitimate race condition in an eventually consistent system. We treat this
            # as success since the desired end state (user gone) matches reality. Nightly
            # reconciliation will clean up any orphaned memberships in our DB.
            logger.info(
                f"User {user_id} not found in Auth0 (deleted between event and processing), skipping membership change"
            )
            return []
        raise

    is_member = any(org.get("id") == org_id for org in user_orgs)

    entities_updated = []

    with Session(engine) as session:
        # Ensure user exists first (events can come out of order)
        existing_user = session.get(User, user_id)
        if not existing_user and is_member:
            # User doesn't exist but should be a member - fetch and create them
            try:
                # user_data = retry_auth0_call(
                #     lambda: auth0_service.get_user_profile(user_id)
                # )
                user_data = auth0_service.get_user_profile(user_id)
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    # 404 during backfill attempt: Events can arrive out of order. We received a
                    # membership event for a user before we received (or processed) the user creation
                    # event. We try to backfill the missing user, but if they've been deleted in Auth0
                    # between the membership event emission and now, we get 404. This is expected in
                    # an eventually consistent event stream. We skip and let reconciliation handle cleanup.
                    logger.info(
                        f"User {user_id} not found in Auth0 when creating during membership processing (deleted between events), skipping"
                    )
                    return []
                raise

            _upsert_user(session, user_data)
            logger.info(f"Created missing user during membership processing: {user_id}")
            entities_updated.append("user")

        # Ensure organization exists (events can come out of order)
        existing_org = session.get(Organization, org_id)
        if not existing_org and is_member:
            # Organization doesn't exist but user should be a member - fetch and create it
            try:
                # org_data = retry_auth0_call(
                #     lambda: auth0_service.get_organization(org_id)
                # )
                org_data = auth0_service.get_organization(org_id)
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    # 404 during backfill attempt: Events can arrive out of order. We received a
                    # membership event for an organization before we received (or processed) the org
                    # creation event. We try to backfill the missing org, but if it's been deleted in
                    # Auth0 between the membership event emission and now, we get 404. This is expected
                    # in an eventually consistent event stream. We skip and let reconciliation handle cleanup.
                    logger.info(
                        f"Organization {org_id} not found in Auth0 when creating during membership processing (deleted between events), skipping"
                    )
                    return []
                raise

            _upsert_organization(session, org_data)
            logger.info(
                f"Created missing organization during membership processing: {org_id}"
            )
            entities_updated.append("organization")

        existing_membership = session.exec(
            select(OrgMembership).where(
                OrgMembership.user_id == user_id, OrgMembership.org_id == org_id
            )
        ).first()

        if is_member and not existing_membership:
            new_membership = OrgMembership(user_id=user_id, org_id=org_id)
            session.add(new_membership)
            logger.info(f"Created membership: {user_id} in {org_id}")
            entities_updated.append("membership")
        elif not is_member and existing_membership:
            session.delete(existing_membership)
            logger.info(f"Removed membership: {user_id} from {org_id}")
            entities_updated.append("membership")
        else:
            logger.info(
                f"Membership unchanged: {user_id} in {org_id} (member={is_member})"
            )

        session.commit()

    return entities_updated


def _handle_api_event(event: Auth0EventBridgeEvent) -> list[str]:
    details = event.detail.data.details or {}
    request = details.get("request", {})
    path = request.get("path", "")

    if not path:
        logger.info("API event missing request path")
        return []

    logger.info(f"Processing API event for path: {path}")

    if "/organizations/" in path and "/members" in path:
        # this only works for organization_member_added
        org_id, user_id = _extract_org_user_from_path(path)
        if request["method"] == "delete" and "/organizations/" in path and "/members" in path:
            logger.info("Detected organization member deletion event")
            org_id = _extract_org_from_path(path)
            user_id = event.detail.data.details.get("request", {}).get("body", {}).get("members", [None])[0]

        logger.info(f"Processing Org {org_id} membership change for {user_id}")
        if org_id and user_id:
            normalized_user_id = normalize_auth0_user_id(user_id)
            if normalized_user_id:
                return _process_membership_change(normalized_user_id, org_id)

    elif path.startswith("/api/v2/users/") and event.detail.data.user_id:
        normalized_user_id = normalize_auth0_user_id(event.detail.data.user_id)
        print(f"normalized_user_id:{normalized_user_id}")
        if normalized_user_id:
            return _process_user_update(normalized_user_id)

    else:
        logger.info(f"Ignoring API event for path: {path}")

    return []


def _extract_org_user_from_path(path: str) -> tuple[str | None, str | None]:
    """Extract organization and user IDs from API path."""
    parts = path.strip("/").split("/")
    try:
        org_index = parts.index("organizations") + 1
        member_index = parts.index("members") + 1
        return parts[org_index], parts[member_index]
    except (ValueError, IndexError):
        return None, None

def _extract_org_from_path(path: str) -> str | None:
    """Extract organization API path."""
    parts = path.strip("/").split("/")
    try:
        org_index = parts.index("organizations") + 1
        # member_index = parts.index("members") + 1
        return parts[org_index]
    except (ValueError, IndexError):
        return None


def _upsert_user(session: Session, user_data: dict[str, Any]) -> None:
    """Update or create user record. Uses timestamp guards to prevent overwriting newer data.

    Timestamp guards protect against out-of-order event processing:
    - If we process a stale event after a newer one, the timestamp check prevents
      overwriting newer data with older data
    - We only update if Auth0's updated_at >= existing record's updated_at
    - This provides ordering guarantees even when events arrive out of order
    """
    user_id = user_data["user_id"]
    email = user_data["email"].lower()
    name = user_data.get("name", email)
    auth0_updated_at = datetime.fromisoformat(user_data["updated_at"])

    existing_user = session.get(User, user_id)

    if existing_user:
        # Only update if our data is newer
        if (
            existing_user.auth0_updated_at is None
            or auth0_updated_at >= existing_user.auth0_updated_at
        ):
            existing_user.email = email
            existing_user.name = name
            existing_user.auth0_updated_at = auth0_updated_at
            logger.debug(f"Updated user: {email}")
        else:
            logger.debug(f"Skipped user update (stale data): {email}")
    else:
        new_user = User(
            id=user_id,
            email=email,
            name=name,
            auth0_updated_at=auth0_updated_at,
        )
        session.add(new_user)
        logger.debug(f"Created user: {email}")


def _upsert_organization(session: Session, org_data: dict[str, Any]) -> None:
    """Update or create organization record. Uses timestamp guards to prevent overwriting newer data."""
    org_id = org_data["id"]
    name = org_data["name"]
    display_name = org_data.get("display_name")
    metadata = org_data.get("metadata", {})

    # Auth0 organizations may not have updated_at field, use current time as fallback
    auth0_updated_at_str = org_data.get("updated_at")
    if auth0_updated_at_str:
        auth0_updated_at = datetime.fromisoformat(auth0_updated_at_str)
    else:
        auth0_updated_at = datetime.now(UTC)

    existing_org = session.get(Organization, org_id)

    if existing_org:
        if (
            existing_org.auth0_updated_at is None
            or auth0_updated_at >= existing_org.auth0_updated_at
        ):
            existing_org.name = name
            existing_org.display_name = display_name
            existing_org.org_metadata = metadata
            existing_org.auth0_updated_at = auth0_updated_at
            logger.debug(f"Updated organization: {name}")
        else:
            logger.debug(f"Skipped organization update (stale data): {name}")
    else:
        new_org = Organization(
            id=org_id,
            name=name,
            display_name=display_name,
            org_metadata=metadata,
            auth0_updated_at=auth0_updated_at,
        )
        session.add(new_org)
        logger.debug(f"Created organization: {name}")
