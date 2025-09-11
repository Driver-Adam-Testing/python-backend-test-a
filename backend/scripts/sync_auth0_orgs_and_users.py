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
import os
import sys
from datetime import UTC, datetime
from typing import Any

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.auth0_service import Auth0Service
from auth0.management import Auth0
from database.db import engine
from database.models import Organization, OrgMembership, User
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
            # Check if organization exists
            existing_org = session.get(Organization, org_id)

            if existing_org:
                # Update existing organization
                existing_org.name = org_name
                existing_org.display_name = org_data.get("display_name")
                existing_org.org_metadata = org_data.get("metadata", {})
                existing_org.synced_at = datetime.utcnow()

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
                    synced_at=datetime.now(UTC),
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
            # Check if user exists
            existing_user = session.get(User, user_id)

            if existing_user:
                # Update existing user
                existing_user.email = email
                existing_user.name = name
                existing_user.synced_at = datetime.utcnow()

                if self.verbose:
                    logger.debug(f"Updated user: {email} ({user_id})")
                self.stats["users_updated"] += 1
            else:
                # Create new user
                new_user = User(
                    id=user_id, email=email, name=name, synced_at=datetime.now(UTC)
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

    def run(self) -> dict[str, Any]:
        """Main sync process."""
        logger.info("Starting Auth0 sync process...")

        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be saved to database")

        try:
            # Get Auth0 client
            auth0_client = self.get_auth0_client()

            # Fetch all data from Auth0
            logger.info("Fetching data from Auth0...")
            organizations = self.fetch_all_organizations(auth0_client)
            users = self.fetch_all_users(auth0_client)

            with Session(engine) as session:
                # Sync organizations
                logger.info("Syncing organizations...")
                for org in organizations:
                    self.sync_organization(session, org)

                # Sync users
                logger.info("Syncing users...")
                for user in users:
                    self.sync_user(session, user)

                # Sync memberships
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
