import logging
from datetime import UTC, datetime
from typing import Any

from app.schemas.auth0_event_schema import (
    Auth0EventBridgeEvent,
    Auth0EventProcessingResult,
    extract_log_id,
)
from app.services.auth0_service import Auth0Service
from app.utils.auth0_retry import retry_auth0_call
from database.db import engine
from database.models import Organization, OrgMembership, User
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


def normalize_auth0_user_id(user_id: str | None) -> str | None:
    """
    Normalize Auth0 user ID to ensure it has the proper prefix.

    Auth0 events sometimes contain user IDs without the provider prefix
    (e.g., "68e58290f57d065d26ae5301" instead of "auth0|68e58290f57d065d26ae5301").
    The Auth0 Management API requires the full format.

    Args:
        user_id: User ID from Auth0 event

    Returns:
        Normalized user ID with proper prefix, or None if input is None/empty
    """
    if not user_id:
        return None

    # If it already has a provider prefix (contains |), return as-is
    if "|" in user_id:
        return user_id

    # If it looks like a standard Auth0 user ID (alphanumeric), prepend auth0|
    if user_id and user_id.replace("_", "").isalnum():
        return f"auth0|{user_id}"

    # For other formats, return as-is and let Auth0 API handle it
    return user_id


def process_auth0_event(event_dict: dict[str, Any]) -> Auth0EventProcessingResult:
    """Process a single Auth0 event. Events are signals - always fetch fresh data from Auth0."""
    try:
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

    except Exception as e:
        logger.error(f"Error processing Auth0 event: {e}", exc_info=True)
        # TODO what do we want to do with failures here? Is mapping them to a result type appropriate for this use case?
        return Auth0EventProcessingResult(
            log_id=event_dict.get("detail", {}).get("log_id", "unknown"),
            event_type=event_dict.get("detail", {})
            .get("data", {})
            .get("type", "unknown"),
            processed=False,
            error=str(e),
        )


def _handle_user_event(event: Auth0EventBridgeEvent) -> list[str]:
    """Handle user create/update events (s, ss)"""
    user_id = normalize_auth0_user_id(event.detail.data.user_id)
    if not user_id:
        logger.warning("User event missing user_id")
        return []

    return _process_user_update(user_id)


def _process_user_update(user_id: str) -> list[str]:
    """Process a user update by fetching fresh data from Auth0."""
    try:
        auth0_service = Auth0Service()
        user_data = retry_auth0_call(lambda: auth0_service.get_user_profile(user_id))

        with Session(engine) as session:
            _upsert_user(session, user_data)
            session.commit()

        logger.info(f"Updated user: {user_id}")
        return ["user"]

    except Exception as e:
        e.add_note(f"Failed to process user update for {user_id}")
        raise


def _handle_user_delete_event(event: Auth0EventBridgeEvent) -> list[str]:
    """Handle user delete events (sdu)"""
    user_id = normalize_auth0_user_id(event.detail.data.user_id)
    if not user_id:
        logger.warning("User delete event missing user_id")
        return []

    try:
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user:
                session.delete(user)

            memberships = session.exec(
                select(OrgMembership).where(OrgMembership.user_id == user_id)
            ).all()

            for membership in memberships:
                session.delete(membership)

            session.commit()

        logger.info(f"Deleted user and memberships: {user_id}")
        return ["user", "membership"]

    except Exception as e:
        e.add_note(f"Failed to handle user delete event for {user_id}")
        raise


def _handle_membership_event(event: Auth0EventBridgeEvent) -> list[str]:
    """Handle organization membership events"""
    user_id = normalize_auth0_user_id(event.detail.data.user_id)
    org_id = event.detail.data.organization_id

    if not user_id or not org_id:
        logger.warning("Membership event missing user_id or org_id")
        return []

    return _process_membership_change(user_id, org_id)


def _process_membership_change(user_id: str, org_id: str) -> list[str]:
    """Process a membership change for the given user and organization."""
    try:
        auth0_service = Auth0Service()
        user_orgs = retry_auth0_call(
            lambda: auth0_service.get_user_organizations(user_id)
        )

        is_member = any(org.get("id") == org_id for org in user_orgs)

        entities_updated = ["membership"]

        with Session(engine) as session:
            # Ensure user exists first (events can come out of order)
            existing_user = session.get(User, user_id)
            if not existing_user and is_member:
                # User doesn't exist but should be a member - fetch and create them
                user_data = retry_auth0_call(
                    lambda: auth0_service.get_user_profile(user_id)
                )
                _upsert_user(session, user_data)
                logger.info(
                    f"Created missing user during membership processing: {user_id}"
                )
                entities_updated.append("user")

            # Ensure organization exists (events can come out of order)
            existing_org = session.get(Organization, org_id)
            if not existing_org and is_member:
                # Organization doesn't exist but user should be a member - fetch and create it
                org_data = retry_auth0_call(
                    lambda: auth0_service.get_organization(org_id)
                )
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
            elif not is_member and existing_membership:
                session.delete(existing_membership)
                logger.info(f"Removed membership: {user_id} from {org_id}")
            else:
                logger.info(
                    f"Membership unchanged: {user_id} in {org_id} (member={is_member})"
                )

            session.commit()

        return entities_updated

    except Exception as e:
        e.add_note(f"Failed to process membership change for {user_id}/{org_id}")
        raise


def _handle_api_event(event: Auth0EventBridgeEvent) -> list[str]:
    """Handle API events by parsing request path"""
    details = event.detail.data.details or {}
    request = details.get("request", {})
    path = request.get("path", "")

    if not path:
        logger.info("API event missing request path")
        return []

    logger.info(f"Processing API event for path: {path}")

    if "/organizations/" in path and "/members" in path:
        org_id, user_id = _extract_org_user_from_path(path)
        if org_id and user_id:
            normalized_user_id = normalize_auth0_user_id(user_id)
            if normalized_user_id:
                return _process_membership_change(normalized_user_id, org_id)

    elif path.startswith("/api/v2/users/") and event.detail.data.user_id:
        normalized_user_id = normalize_auth0_user_id(event.detail.data.user_id)
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


def _upsert_user(session: Session, user_data: dict[str, Any]) -> None:
    """Update or create user record. Uses timestamp guards to prevent overwriting newer data."""
    user_id = user_data.get("user_id")
    if not user_id:
        logger.warning("User data missing user_id")
        return

    email = user_data.get("email", "").lower()
    name = user_data.get("name", email)

    auth0_updated_at = user_data.get("updated_at")
    if auth0_updated_at:
        if auth0_updated_at.endswith("Z"):
            auth0_updated_at = auth0_updated_at[:-1] + "+00:00"
        try:
            auth0_updated_at = datetime.fromisoformat(auth0_updated_at)
        except ValueError:
            auth0_updated_at = datetime.now(UTC)
    else:
        auth0_updated_at = datetime.now(UTC)

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
    org_id = org_data.get("id")
    if not org_id:
        logger.warning("Organization data missing id")
        return

    name = org_data.get("name")
    display_name = org_data.get("display_name")
    metadata = org_data.get("metadata", {})

    if not name:
        logger.warning(f"Organization {org_id} missing name")
        return

    existing_org = session.get(Organization, org_id)

    if existing_org:
        existing_org.name = name
        existing_org.display_name = display_name
        existing_org.org_metadata = metadata
        existing_org.auth0_updated_at = datetime.now(UTC)
        logger.debug(f"Updated organization: {name}")
    else:
        new_org = Organization(
            id=org_id,
            name=name,
            display_name=display_name,
            org_metadata=metadata,
            auth0_updated_at=datetime.now(UTC),
        )
        session.add(new_org)
        logger.debug(f"Created organization: {name}")
