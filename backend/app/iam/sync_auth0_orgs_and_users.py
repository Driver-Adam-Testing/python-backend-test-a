#!/usr/bin/env python
"""
Sync Auth0 organizations and users to the local database.

This script fetches all organizations and users from Auth0 and syncs them
to the local database tables (organizations, users, org_memberships).

Usage:
    python sync_auth0_orgs_and_users.py [--dry-run] [--verbose]
"""

import argparse
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.services.auth0_service import Auth0Service
from auth0.management import Auth0
from database.db import engine
from database.models import Auth0SyncRun, Organization, OrgMembership, User
from sqlmodel import Session, select

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Auth0Sync:
    """Handles syncing Auth0 data to local database."""

    def __init__(self, dry_run: bool = False, verbose: bool = False) -> None:
        self.dry_run = dry_run
        self.verbose = verbose
        self.auth0_service = Auth0Service()
        self.stats = {
            "orgs_created": 0,
            "orgs_updated": 0,
            "orgs_skipped": 0,
            "users_created": 0,
            "users_updated": 0,
            "users_skipped": 0,
            "memberships_created": 0,
            "memberships_skipped": 0,
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

    def fetch_all_users(
        self, auth0_client: Auth0, last_sync_timestamp: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Fetch users from Auth0 with pagination, optionally filtering by updated_at."""
        users = []
        page = 0
        per_page = 100

        # Build query for incremental sync
        query = None
        if last_sync_timestamp:
            # Format timestamp for Auth0 Lucene query
            timestamp_str = (
                last_sync_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            )
            query = f"updated_at:[{timestamp_str} TO *]"
            logger.info(
                f"Incremental sync: fetching users updated since {timestamp_str}"
            )

        while True:
            try:
                if query:
                    response = auth0_client.users.list(
                        q=query, per_page=per_page, page=page
                    )
                else:
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

        sync_type = "incremental" if last_sync_timestamp else "full"
        logger.info(f"Fetched {len(users)} users from Auth0 ({sync_type} sync)")
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
            # Check if organization exists
            existing_org = session.get(Organization, org_id)

            if existing_org:
                # Update existing organization
                existing_org.name = org_name
                existing_org.display_name = org_data.get("display_name")
                existing_org.org_metadata = org_data.get("metadata", {})
                existing_org.auth0_updated_at = datetime.now(UTC)

                if self.verbose:
                    logger.debug(f"Updated organization: {org_name} ({org_id})")
                self.stats["orgs_updated"] += 1
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
        auth0_updated_at = user_data.get("updated_at", datetime.now(UTC))

        if not user_id:
            logger.warning(f"Skipping user with missing id: {user_data}")
            self.stats["users_skipped"] += 1
            return False

        try:
            # Check if user exists by id
            existing_user = session.get(User, user_id)

            if existing_user:
                # Update existing user
                existing_user.email = email
                existing_user.name = name
                existing_user.auth0_updated_at = auth0_updated_at

                if self.verbose:
                    logger.debug(f"Updated user: {email} ({user_id})")
                self.stats["users_updated"] += 1
            else:
                # Create new user
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
                new_membership = OrgMembership(org_id=org_id, user_id=user_id)
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

    # TODO: use auth0 updated_at field to populate org,user sync timestamps
    def run(self) -> dict[str, Any]:
        """Main sync process."""
        logger.info("Starting Auth0 sync process...")

        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be saved to database")

        sync_run_id = None
        last_sync_timestamp = None
        try:
            with Session(engine) as session:
                # Get the last successful sync timestamp
                last_sync = session.exec(
                    select(Auth0SyncRun)
                    .where(Auth0SyncRun.status == "synced")
                    .order_by(Auth0SyncRun.timestamp.desc())
                ).first()

                # Store the timestamp before closing session
                if last_sync:
                    last_sync_timestamp = last_sync.timestamp

                # Create new sync run record with current timestamp
                current_timestamp = datetime.now(UTC)
                sync_run = Auth0SyncRun(timestamp=current_timestamp, status="syncing")
                session.add(sync_run)
                session.commit()

                # Store the ID for later use
                sync_run_id = sync_run.id

                sync_type = "incremental" if last_sync else "full"
                logger.info(f"Running {sync_type} sync")
                if last_sync:
                    logger.info(
                        f"Last successful sync: {last_sync.timestamp.isoformat()}"
                    )

            # Get Auth0 client
            auth0_client = self.get_auth0_client()

            # Fetch data from Auth0
            logger.info("Fetching data from Auth0...")
            organizations = self.fetch_all_organizations(auth0_client)

            # Use last sync timestamp for incremental user fetch
            users = self.fetch_all_users(auth0_client, last_sync_timestamp)

            with Session(engine) as session:
                # Sync organizations (always do all orgs since we can't filter them)
                logger.info("Syncing organizations...")
                for org in organizations:
                    self.sync_organization(session, org)

                # Sync users
                logger.info("Syncing users...")
                for user in users:
                    self.sync_user(session, user)

                # Sync memberships (only for changed users in incremental mode)
                logger.info("Syncing organization memberships...")
                for user in users:
                    user_id = user.get("user_id")
                    if not user_id:
                        continue

                    # Get user's organizations
                    user_orgs = self.fetch_user_organizations(auth0_client, user_id)

                    for org in user_orgs:
                        org_id = org.get("id")
                        if org_id:
                            self.sync_membership(session, org_id, user_id)

                # Mark sync as complete
                if sync_run_id and not self.dry_run:
                    sync_run_in_session = session.get(Auth0SyncRun, sync_run_id)
                    if sync_run_in_session:
                        sync_run_in_session.status = "synced"

                # Commit or rollback
                if self.dry_run:
                    logger.info("Dry run - rolling back all changes")
                    session.rollback()
                else:
                    logger.info("Committing changes to database")
                    session.commit()

        except Exception as e:
            logger.error(f"Fatal error during sync: {e}")
            self.stats["errors"].append(f"Fatal error: {e!s}")

            # Note: Failed syncs remain in "syncing" status to indicate incompletion
            # No need to update the sync_run record since it already has status="syncing"

        # Print summary
        self.print_summary()

        return self.stats

    def print_summary(self) -> None:
        """Print sync summary statistics."""
        print("\n" + "=" * 60)
        print("SYNC SUMMARY")
        print("=" * 60)

        if self.dry_run:
            print("DRY RUN - No changes were saved")
            print("-" * 60)

        print("Organizations:")
        print(f"  Created: {self.stats['orgs_created']}")
        print(f"  Updated: {self.stats['orgs_updated']}")
        print(f"  Skipped: {self.stats['orgs_skipped']}")

        print("\nUsers:")
        print(f"  Created: {self.stats['users_created']}")
        print(f"  Updated: {self.stats['users_updated']}")
        print(f"  Skipped: {self.stats['users_skipped']}")

        print("\nMemberships:")
        print(f"  Created: {self.stats['memberships_created']}")
        print(f"  Skipped: {self.stats['memberships_skipped']}")

        if self.stats["errors"]:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats["errors"]) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")

        print("=" * 60 + "\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync Auth0 organizations and users to local database"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without saving changes to database"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Run sync
    syncer = Auth0Sync(dry_run=args.dry_run, verbose=args.verbose)
    stats = syncer.run()

    # Exit with error code if there were errors
    if stats["errors"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
