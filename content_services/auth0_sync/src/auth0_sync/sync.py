"""
Auth0 Reconciliation Script - Full Sync with Deletion Detection

This script performs a complete reconciliation between Auth0 and the local database:
- Fetches ALL organizations, users, and memberships from Auth0
- Creates/updates entities that exist in Auth0
- Deletes entities that exist in DB but not in Auth0 (Auth0 is source of truth)
- Uses timestamp guards to prevent overwriting newer data with older data

This should run regularly (nightly minimum) to:
- Catch events that were missed or failed to process
- Detect and fix divergence between Auth0 and DB
- Ensure DB stays in sync with Auth0 as the authoritative source
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any

from auth0.management import Auth0
from database.db import engine
from database.models import Auth0SyncRun, Organization, OrgMembership, OrgRole, User
from shared.auth0.auth0_service import Auth0Service
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


class Auth0Sync:
    """Handles syncing Auth0 data to local database."""

    def __init__(self, dry_run: bool = False, verbose: bool = False) -> None:
        self.dry_run = dry_run
        self.verbose = verbose
        self.auth0_service = Auth0Service(
            # TODO could use settings module as in other modal func in the app
            os.environ["AUTH0_MGMT_API_DOMAIN"],
            os.environ["AUTH0_MGMT_API_CLIENT_ID"],
            os.environ["AUTH0_MGMT_API_CLIENT_SECRET"],
            os.environ["AUTH0_DOMAIN"],
            os.environ["AUTH0_CLIENT_ID"],
            timeout=30.0,
        )
        self.stats = {
            "orgs_created": 0,
            "orgs_updated": 0,
            "orgs_skipped": 0,
            "orgs_deleted": 0,
            "users_created": 0,
            "users_updated": 0,
            "users_skipped": 0,
            "users_deleted": 0,
            "memberships_created": 0,
            "memberships_skipped": 0,
            "memberships_deleted": 0,
            "errors": [],
        }

        if self.verbose:
            logger.setLevel(logging.DEBUG)

    def get_auth0_client(self) -> Auth0:
        """Get authenticated Auth0 management client."""
        mgmt_api_token = self.auth0_service.get_mgmt_api_token()
        return Auth0(self.auth0_service.auth0_mgmt_domain, mgmt_api_token)

    def fetch_all_organizations(self, auth0_client: Auth0) -> list[dict[str, Any]]:
        """Fetch all organizations from Auth0 with pagination."""
        organizations = []
        page = 0
        per_page = 100

        while True:
            try:
                response = auth0_client.organizations.all_organizations(
                    per_page=per_page, page=page
                )
                batch = response.get("organizations", [])

                if not batch:
                    break

                organizations.extend(batch)
                page += 1

                if self.verbose:
                    logger.debug(f"Fetched page {page} with {len(batch)} organizations")

            except Exception as e:
                logger.error(f"Error fetching organizations page {page}: {e}")
                self.stats["errors"].append(f"Failed to fetch orgs page {page}: {e!s}")
                break

        logger.info(f"Fetched {len(organizations)} organizations from Auth0")
        return organizations

    def fetch_all_users(self, auth0_client: Auth0) -> list[dict[str, Any]]:
        """Fetch all users from Auth0 with pagination."""
        users = []
        page = 0
        per_page = 100

        while True:
            try:
                response = auth0_client.users.list(per_page=per_page, page=page)
                batch = response.get("users", [])

                if not batch:
                    break

                users.extend(batch)
                page += 1

                if self.verbose:
                    logger.debug(f"Fetched page {page} with {len(batch)} users")

            except Exception as e:
                logger.error(f"Error fetching users page {page}: {e}")
                self.stats["errors"].append(f"Failed to fetch users page {page}: {e!s}")
                break

        logger.info(f"Fetched {len(users)} users from Auth0")
        return users

    def fetch_user_organizations(
        self, auth0_client: Auth0, user_id: str
    ) -> list[dict[str, Any]]:
        """Fetch all organizations for a specific user."""
        organizations = []
        page = 0
        per_page = 100

        while True:
            try:
                response = auth0_client.users.list_organizations(
                    user_id, per_page=per_page, page=page
                )
                batch = response.get("organizations", [])

                if not batch:
                    break

                organizations.extend(batch)
                page += 1

            except Exception as e:
                logger.error(f"Error fetching orgs for user {user_id}: {e}")
                self.stats["errors"].append(
                    f"Failed to fetch orgs for user {user_id}: {e!s}"
                )
                break

        return organizations

    def sync_organization(self, session: Session, org_data: dict[str, Any]) -> bool:
        """Sync a single organization to the database."""
        org_id = org_data.get("id")
        org_name = org_data.get("name")

        if not org_id or not org_name:
            logger.warning(f"Skipping org with missing id or name: {org_data}")
            self.stats["orgs_skipped"] += 1
            return False

        try:
            existing_org = session.get(Organization, org_id)

            if existing_org:
                data_is_changed = (
                    existing_org.name != org_name
                    or existing_org.display_name != org_data.get("display_name")
                    or existing_org.org_metadata != org_data.get("metadata", {})
                )
                if data_is_changed:
                    existing_org.name = org_name
                    existing_org.display_name = org_data.get("display_name")
                    existing_org.org_metadata = org_data.get("metadata", {})
                    existing_org.auth0_updated_at = (
                        None  # Auth0 doesn't provide updated_at for orgs
                    )
                    session.add(existing_org)

                    if self.verbose:
                        logger.debug(f"Updated organization: {org_name} ({org_id})")
                    self.stats["orgs_updated"] += 1
                else:
                    if self.verbose:
                        logger.debug(
                            f"Skipped unchanged organization: {org_name} ({org_id})"
                        )
                    self.stats["orgs_skipped"] += 1

            else:
                new_org = Organization(
                    id=org_id,
                    name=org_name,
                    display_name=org_data.get("display_name"),
                    org_metadata=org_data.get("metadata", {}),
                    auth0_updated_at=None,  # Auth0 doesn't provide updated_at for orgs
                )
                session.add(new_org)

                if self.verbose:
                    logger.debug(f"Created organization: {org_name} ({org_id})")
                self.stats["orgs_created"] += 1

            return True

        except Exception as e:
            logger.error(f"Error syncing organization {org_id}: {e}")
            self.stats["errors"].append(f"Failed to sync org {org_id}: {e!s}")
            return False

    def sync_user(self, session: Session, user_data: dict[str, Any]) -> bool:
        """Sync a single user to the database."""
        user_id = user_data.get("user_id")
        email = user_data.get("email", "").lower()
        name = user_data.get("name", email)

        if not user_id:
            logger.warning(f"Skipping user with missing id: {user_data}")
            self.stats["users_skipped"] += 1
            return False

        try:
            auth0_updated_at = datetime.fromisoformat(user_data["updated_at"])

            existing_user = session.get(User, user_id)

            if existing_user:
                timestamp_is_newer = (
                    existing_user.auth0_updated_at is None
                    or auth0_updated_at > existing_user.auth0_updated_at
                )

                if timestamp_is_newer:
                    data_changed = (
                        existing_user.name != name or existing_user.email != email
                    )
                    if data_changed:
                        existing_user.email = email
                        existing_user.name = name
                    # Always update timestamp if Auth0 sent newer data
                    existing_user.auth0_updated_at = auth0_updated_at
                    session.add(existing_user)

                    if self.verbose:
                        logger.debug(f"Updated user: {email} ({user_id})")
                    self.stats["users_updated"] += 1
                else:
                    if self.verbose:
                        logger.debug(f"Skipped stale user data: {email} ({user_id})")
                    self.stats["users_skipped"] += 1
            else:
                new_user = User(
                    id=user_id,
                    email=email,
                    name=name,
                    auth0_updated_at=auth0_updated_at,
                )
                session.add(new_user)

                if self.verbose:
                    logger.debug(f"Created user: {email} ({user_id})")
                self.stats["users_created"] += 1

            return True

        except Exception as e:
            logger.error(f"Error syncing user {user_id}: {e}")
            self.stats["errors"].append(f"Failed to sync user {user_id}: {e!s}")
            return False

    def sync_membership(self, session: Session, org_id: str, user_id: str) -> bool:
        """Create or update organization membership."""
        try:
            # Check if membership already exists
            existing_membership = session.exec(
                select(OrgMembership).where(
                    OrgMembership.org_id == org_id, OrgMembership.user_id == user_id
                )
            ).first()

            if existing_membership:
                if self.verbose:
                    logger.debug(f"Membership already exists: {user_id} in {org_id}")
                self.stats["memberships_skipped"] += 1
            else:
                # Create new membership
                new_membership = OrgMembership(
                    org_id=org_id, user_id=user_id, role=OrgRole.member
                )
                session.add(new_membership)

                if self.verbose:
                    logger.debug(f"Created membership: {user_id} in {org_id}")
                self.stats["memberships_created"] += 1

            return True

        except Exception as e:
            logger.error(f"Error syncing membership {user_id} in {org_id}: {e}")
            self.stats["errors"].append(
                f"Failed to sync membership {user_id} in {org_id}: {e!s}"
            )
            return False

    def delete_stale_memberships(
        self, session: Session, auth0_memberships: set[tuple[str, str]]
    ) -> None:
        """Delete memberships that exist in DB but not in Auth0."""
        db_memberships = session.exec(select(OrgMembership)).all()

        for membership in db_memberships:
            membership_tuple = (membership.org_id, membership.user_id)
            if membership_tuple not in auth0_memberships:
                session.delete(membership)
                if self.verbose:
                    logger.debug(
                        f"Deleted stale membership: {membership.user_id} in {membership.org_id}"
                    )
                self.stats["memberships_deleted"] += 1

    def delete_stale_users(self, session: Session, auth0_user_ids: set[str]) -> None:
        """Delete users that exist in DB but not in Auth0."""
        db_users = session.exec(select(User)).all()

        for user in db_users:
            if user.id not in auth0_user_ids:
                session.delete(user)
                if self.verbose:
                    logger.debug(f"Deleted stale user: {user.email} ({user.id})")
                self.stats["users_deleted"] += 1

    def delete_stale_organizations(
        self, session: Session, auth0_org_ids: set[str]
    ) -> None:
        """Delete organizations that exist in DB but not in Auth0."""
        db_orgs = session.exec(select(Organization)).all()

        for org in db_orgs:
            if org.id not in auth0_org_ids:
                session.delete(org)
                if self.verbose:
                    logger.debug(f"Deleted stale organization: {org.name} ({org.id})")
                self.stats["orgs_deleted"] += 1

    def run(self) -> dict[str, Any]:
        logger.info("Starting Auth0 full reconciliation...")

        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be saved to database")

        sync_run_id = None

        if not self.dry_run:
            with Session(engine) as session:
                current_timestamp = datetime.now(UTC)
                sync_run = Auth0SyncRun(timestamp=current_timestamp, status="syncing")
                session.add(sync_run)
                session.commit()
                sync_run_id = sync_run.id
                logger.info(f"Created sync run record: {sync_run_id}")

        try:
            self._run_reconciliation()

            if sync_run_id:
                with Session(engine) as session:
                    sync_run = session.get(Auth0SyncRun, sync_run_id)
                    if sync_run:
                        sync_run.status = "synced"
                        session.commit()
                        logger.info(f"Marked sync run {sync_run_id} as successful")

        except Exception as e:
            logger.error(f"Fatal error during reconciliation: {e}")
            self.stats["errors"].append(f"Fatal error: {e!s}")

            # Mark sync as failed
            if sync_run_id:
                with Session(engine) as session:
                    sync_run = session.get(Auth0SyncRun, sync_run_id)
                    if sync_run:
                        sync_run.status = "error"
                        session.commit()
                        logger.error(f"Marked sync run {sync_run_id} as failed")

        self.print_summary()
        return self.stats

    def _run_reconciliation(self) -> None:
        """Execute the actual reconciliation logic."""
        auth0_client = self.get_auth0_client()

        logger.info("Phase 1: Fetching all data from Auth0...")

        logger.info("Fetching all organizations from Auth0...")
        organizations = self.fetch_all_organizations(auth0_client)

        logger.info("Fetching all users from Auth0...")
        users = self.fetch_all_users(auth0_client)

        logger.info("Fetching all user-org memberships from Auth0...")
        auth0_memberships: set[tuple[str, str]] = set()
        for user in users:
            user_id = user.get("user_id")
            if not user_id:
                continue
            user_orgs = self.fetch_user_organizations(auth0_client, user_id)
            for org in user_orgs:
                org_id = org.get("id")
                if org_id:
                    auth0_memberships.add((org_id, user_id))

        if self.stats["errors"]:
            error_count = len(self.stats["errors"])
            raise RuntimeError(
                f"Failed to fetch complete data from Auth0: {error_count} errors occurred. "
                "Aborting reconciliation to prevent data corruption."
            )

        if len(organizations) == 0:
            raise RuntimeError(
                "Fetched 0 organizations from Auth0. This is unexpected. "
                "Aborting reconciliation to prevent deleting all organizations."
            )

        if len(users) == 0:
            raise RuntimeError(
                "Fetched 0 users from Auth0. This is unexpected. "
                "Aborting reconciliation to prevent deleting all users."
            )

        logger.info(
            f"Validation passed: {len(organizations)} orgs, {len(users)} users, "
            f"{len(auth0_memberships)} memberships"
        )

        auth0_org_ids = {org["id"] for org in organizations if org.get("id")}
        auth0_user_ids = {user["user_id"] for user in users if user.get("user_id")}

        # Phase 3: Sync to database (single atomic transaction)
        logger.info("Phase 3: Syncing to database...")
        with Session(engine) as session:
            logger.info("Syncing organizations...")
            for org in organizations:
                self.sync_organization(session, org)

            logger.info("Syncing users...")
            for user in users:
                self.sync_user(session, user)

            logger.info("Syncing organization memberships...")
            for org_id, user_id in auth0_memberships:
                self.sync_membership(session, org_id, user_id)

            logger.info("Deleting stale memberships...")
            self.delete_stale_memberships(session, auth0_memberships)

            logger.info("Deleting stale users...")
            self.delete_stale_users(session, auth0_user_ids)

            logger.info("Deleting stale organizations...")
            self.delete_stale_organizations(session, auth0_org_ids)

            if self.dry_run:
                logger.info("Dry run - rolling back all changes")
                session.rollback()
            else:
                logger.info("Committing changes to database")
                session.commit()

    def print_summary(self) -> None:
        """Print sync summary statistics."""
        print("\n" + "=" * 60)
        print("RECONCILIATION SUMMARY")
        print("=" * 60)

        if self.dry_run:
            print("DRY RUN - No changes were saved")
            print("-" * 60)

        print("Organizations:")
        print(f"  Created: {self.stats['orgs_created']}")
        print(f"  Updated: {self.stats['orgs_updated']}")
        print(f"  Skipped: {self.stats['orgs_skipped']}")
        print(f"  Deleted: {self.stats['orgs_deleted']}")

        print("\nUsers:")
        print(f"  Created: {self.stats['users_created']}")
        print(f"  Updated: {self.stats['users_updated']}")
        print(f"  Skipped: {self.stats['users_skipped']}")
        print(f"  Deleted: {self.stats['users_deleted']}")

        print("\nMemberships:")
        print(f"  Created: {self.stats['memberships_created']}")
        print(f"  Skipped: {self.stats['memberships_skipped']}")
        print(f"  Deleted: {self.stats['memberships_deleted']}")

        # Calculate divergence
        total_changes = (
            self.stats["orgs_created"]
            + self.stats["orgs_updated"]
            + self.stats["orgs_deleted"]
            + self.stats["users_created"]
            + self.stats["users_updated"]
            + self.stats["users_deleted"]
            + self.stats["memberships_created"]
            + self.stats["memberships_deleted"]
        )
        if total_changes > 0:
            print(f"\nTotal divergence corrections: {total_changes}")

        if self.stats["errors"]:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats["errors"]) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")

        print("=" * 60 + "\n")
