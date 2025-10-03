#!/usr/bin/env python
"""
Incremental Auth0 sync utilities for webhook events.

This module provides functions to sync individual Auth0 entities
when webhook events are received, rather than doing a full sync.

Usage:
    from auth0_incremental_sync import sync_single_user, sync_single_organization
"""

import logging
from datetime import UTC, datetime
from typing import Any

from app.services.auth0_service import Auth0Service
from database.db import engine
from database.models import Auth0SyncRun, Organization, OrgMembership, User
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


def sync_single_organization(org_id: str, session: Session | None = None) -> bool:
    """
    Sync a single organization from Auth0 to the database.

    Args:
        org_id: The Auth0 organization ID
        session: Optional database session (will create one if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        auth0_service = Auth0Service()

        # Fetch organization from Auth0
        org_data = auth0_service.get_organization(org_id)

        if not org_data:
            logger.error(f"Organization {org_id} not found in Auth0")
            return False

        # Use provided session or create a new one
        if session:
            return _sync_org_to_db(session, org_data)
        else:
            with Session(engine) as new_session:
                result = _sync_org_to_db(new_session, org_data)
                new_session.commit()
                return result

    except Exception as e:
        logger.error(f"Error syncing organization {org_id}: {e}")
        return False


def sync_single_user(user_id: str, session: Session | None = None) -> bool:
    """
    Sync a single user from Auth0 to the database.

    Args:
        user_id: The Auth0 user ID
        session: Optional database session (will create one if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        auth0_service = Auth0Service()
        auth0_client = auth0_service._management_client()

        # Fetch user from Auth0
        user_data = auth0_client.users.get(user_id)

        if not user_data:
            logger.error(f"User {user_id} not found in Auth0")
            return False

        # Use provided session or create a new one
        if session:
            return _sync_user_to_db(session, user_data)
        else:
            with Session(engine) as new_session:
                result = _sync_user_to_db(new_session, user_data)
                new_session.commit()
                return result

    except Exception as e:
        logger.error(f"Error syncing user {user_id}: {e}")
        return False


def sync_user_membership(
    user_id: str, org_id: str, action: str = "add", session: Session | None = None
) -> bool:
    """
    Sync a user's membership in an organization.

    Args:
        user_id: The Auth0 user ID
        org_id: The Auth0 organization ID
        action: "add" or "remove"
        session: Optional database session (will create one if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Use provided session or create a new one
        if session:
            return _sync_membership_to_db(session, user_id, org_id, action)
        else:
            with Session(engine) as new_session:
                result = _sync_membership_to_db(new_session, user_id, org_id, action)
                new_session.commit()
                return result

    except Exception as e:
        logger.error(f"Error syncing membership {user_id} in {org_id}: {e}")
        return False


def sync_user_with_organizations(user_id: str, session: Session | None = None) -> bool:
    """
    Sync a user and all their organization memberships.

    Args:
        user_id: The Auth0 user ID
        session: Optional database session (will create one if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        auth0_service = Auth0Service()
        auth0_client = auth0_service._management_client()

        # Use provided session or create a new one
        should_commit = session is None
        working_session = session or Session(engine)

        try:
            # Sync user
            user_data = auth0_client.users.get(user_id)
            if not _sync_user_to_db(working_session, user_data):
                return False

            # Get user's organizations
            organizations = []
            page = 0
            per_page = 100

            while True:
                response = auth0_client.users.list_organizations(
                    user_id, per_page=per_page, page=page
                )
                batch = response.get("organizations", [])

                if not batch:
                    break

                organizations.extend(batch)
                page += 1

            # Sync each organization and membership
            for org_data in organizations:
                org_id = org_data.get("id")
                if org_id:
                    # Ensure organization exists
                    _sync_org_to_db(working_session, org_data)
                    # Create membership
                    _sync_membership_to_db(working_session, user_id, org_id, "add")

            # Remove memberships that don't exist in Auth0
            current_org_ids = {org.get("id") for org in organizations if org.get("id")}

            # Query memberships by user_id directly (which is now the Auth0 user ID)
            existing_memberships = working_session.exec(
                select(OrgMembership).where(OrgMembership.user_id == user_id)
            ).all()

            for membership in existing_memberships:
                if membership.org_id not in current_org_ids:
                    logger.info(
                        f"Removing outdated membership: {user_id} from {membership.org_id}"
                    )
                    working_session.delete(membership)

            if should_commit:
                working_session.commit()

            return True

        finally:
            if should_commit:
                working_session.close()

    except Exception as e:
        logger.error(f"Error syncing user with organizations {user_id}: {e}")
        return False


# Private helper functions


def _sync_org_to_db(session: Session, org_data: dict[str, Any]) -> bool:
    """Internal function to sync organization data to database."""
    org_id = org_data.get("id")
    org_name = org_data.get("name")

    if not org_id or not org_name:
        logger.warning(f"Skipping org with missing id or name: {org_data}")
        return False

    existing_org = session.get(Organization, org_id)

    if existing_org:
        # Update existing organization
        existing_org.name = org_name
        existing_org.display_name = org_data.get("display_name")
        existing_org.org_metadata = org_data.get("metadata", {})
        existing_org.auth0_updated_at = datetime.now(UTC)
        logger.info(f"Updated organization: {org_name} ({org_id})")
    else:
        # Create new organization
        new_org = Organization(
            id=org_id,
            name=org_name,
            display_name=org_data.get("display_name"),
            org_metadata=org_data.get("metadata", {}),
            auth0_updated_at=datetime.now(UTC),
        )
        session.add(new_org)
        logger.info(f"Created organization: {org_name} ({org_id})")

    return True


def _sync_user_to_db(session: Session, user_data: dict[str, Any]) -> bool:
    """Internal function to sync user data to database."""
    user_id = user_data.get("user_id")
    email = user_data.get("email", "").lower()
    name = user_data.get("name", email)

    if not user_id:
        logger.warning(f"Skipping user with missing id: {user_data}")
        return False

    existing_user = session.get(User, user_id)

    if existing_user:
        # Update existing user
        existing_user.email = email
        existing_user.name = name
        existing_user.auth0_updated_at = datetime.now(UTC)
        logger.info(f"Updated user: {email} ({user_id})")
    else:
        # Create new user
        new_user = User(
            id=user_id,
            email=email,
            name=name,
            auth0_updated_at=datetime.now(UTC),
        )
        session.add(new_user)
        logger.info(f"Created user: {email} ({user_id})")

    return True


def _sync_membership_to_db(
    session: Session, user_id: str, org_id: str, action: str
) -> bool:
    """Internal function to sync membership data to database."""
    if action == "add":
        # Check if membership already exists
        existing_membership = session.exec(
            select(OrgMembership).where(
                OrgMembership.org_id == org_id, OrgMembership.user_id == user_id
            )
        ).first()

        if not existing_membership:
            # Create new membership
            new_membership = OrgMembership(org_id=org_id, user_id=user_id)
            session.add(new_membership)
            logger.info(f"Created membership: {user_id} in {org_id}")
        else:
            logger.debug(f"Membership already exists: {user_id} in {org_id}")

    elif action == "remove":
        # Remove membership
        membership = session.exec(
            select(OrgMembership).where(
                OrgMembership.org_id == org_id, OrgMembership.user_id == user_id
            )
        ).first()

        if membership:
            session.delete(membership)
            logger.info(f"Removed membership: {user_id} from {org_id}")
        else:
            logger.debug(f"Membership not found to remove: {user_id} from {org_id}")

    return True


# Example webhook handler
def handle_auth0_webhook(event_type: str, payload: dict[str, Any]) -> bool:
    """
    Handle Auth0 webhook events and track them in Auth0SyncRun.

    Args:
        event_type: The type of Auth0 event
        payload: The webhook payload

    Returns:
        True if handled successfully, False otherwise
    """
    logger.info(f"Handling Auth0 webhook: {event_type}")

    sync_run = None
    try:
        with Session(engine) as session:
            # Create sync run record
            current_timestamp = datetime.now(UTC)
            sync_run = Auth0SyncRun(timestamp=current_timestamp, status="syncing")
            session.add(sync_run)
            session.commit()

            # Process the webhook event
            result = False
            if event_type == "user.created" or event_type == "user.updated":
                user_id = payload.get("user_id")
                if user_id:
                    result = sync_single_user(user_id, session)

            elif (
                event_type == "organization.created"
                or event_type == "organization.updated"
            ):
                org_id = payload.get("id")
                if org_id:
                    result = sync_single_organization(org_id, session)

            elif event_type == "organization.member_added":
                user_id = payload.get("user_id")
                org_id = payload.get("organization_id")
                if user_id and org_id:
                    result = sync_user_membership(user_id, org_id, "add", session)

            elif event_type == "organization.member_removed":
                user_id = payload.get("user_id")
                org_id = payload.get("organization_id")
                if user_id and org_id:
                    result = sync_user_membership(user_id, org_id, "remove", session)

            else:
                logger.warning(f"Unhandled Auth0 event type: {event_type}")
                session.rollback()
                return False

            # Mark sync as complete if successful
            if result and sync_run:
                sync_run_in_session = session.get(Auth0SyncRun, sync_run.id)
                if sync_run_in_session:
                    sync_run_in_session.status = "synced"

            # Commit or rollback based on result
            if result:
                session.commit()
                return True
            else:
                session.rollback()
                return False

    except Exception as e:
        logger.error(f"Error handling Auth0 webhook {event_type}: {e}")
        return False
