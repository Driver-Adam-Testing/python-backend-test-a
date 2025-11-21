#!/usr/bin/env python3
"""
Auth0 Organization Setup CLI

This script automates the creation and setup of Auth0 organizations.
It replicates the logic from the signup endpoint but for administrative use.

Usage:
    python scripts/setup_org.py
    python scripts/setup_org.py --dry-run
"""

import argparse
import logging
import os
import sys

# Add the project root to the python path so we can import app modules
# Current file: backend/scripts/setup_org.py
# We need to add 'backend' (parent dir) to path to import 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# We need to add 'packages/shared' to path to import 'shared'
# backend/scripts/ -> ../../packages/shared
sys.path.append(os.path.join(os.path.dirname(__file__), "../../packages/shared"))

from app.services.auth0_factory import create_auth0_service

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def setup_org(
    org_name: str, display_name: str, admin_email: str, dry_run: bool = False
) -> None:
    """
    Creates an Auth0 organization, enables the default connection, and invites the admin.
    """
    logger.info(f"Starting organization setup for '{display_name}' ({org_name})")
    logger.info(f"Admin Email: {admin_email}")

    if dry_run:
        logger.info("[DRY RUN] Would initialize Auth0Service")
    else:
        try:
            service = create_auth0_service()
        except Exception as e:
            logger.error(f"Failed to initialize Auth0Service: {e}")
            return

    # 1. Create Organization
    if dry_run:
        logger.info(
            f"[DRY RUN] Would create organization: name='{org_name}', display_name='{display_name}'"
        )
        # Mock org object for subsequent steps in dry run
        org = {"id": "org_mock_id"}
    else:
        try:
            org = service.create_organization(
                name=org_name,
                display_name=display_name,
                metadata={
                    "self_service": "false"
                },  # Created via CLI, so not self-service
            )
            logger.info(f"Successfully created organization: {org['id']}")
        except Exception as e:
            logger.error(f"Failed to create organization: {e}")
            return

    # 2. Enable Username-Password-Authentication connection
    if dry_run:
        logger.info(
            f"[DRY RUN] Would enable 'Username-Password-Authentication' connection for org {org['id']}"
        )
    else:
        try:
            conn_id = service.get_username_password_connection_id()
            service.enable_connection_for_organization(
                org_id=org["id"], connection_id=conn_id
            )
            logger.info(
                f"Enabled 'Username-Password-Authentication' connection for org {org['id']}"
            )
        except Exception as e:
            logger.error(f"Failed to enable connection: {e}")
            # Attempt cleanup?
            return

    # 3. Invite Admin with org_super_admin role
    role_name = "org_super_admin"
    if dry_run:
        logger.info(
            f"[DRY RUN] Would invite '{admin_email}' to org {org['id']} with role '{role_name}' via create_admin_invite"
        )
    else:
        try:
            # No need to look up role ID anymore, create_admin_invite uses the role name directly
            # in app_metadata.

            # Note: create_admin_invite expects the role name (e.g. "org_super_admin"),
            # NOT the role ID. The logic inside create_admin_invite puts it into app_metadata.
            service.create_admin_invite(
                org_id=org["id"],
                email=admin_email,
                role_name=role_name,
            )
            logger.info(
                f"Invited {admin_email} to organization with role '{role_name}'"
            )
        except Exception as e:
            logger.error(f"Failed to invite admin: {e}")
            # Attempt cleanup
            try:
                logger.info(f"Attempting to cleanup organization {org['id']}...")
                service.delete_organization(org["id"])
                logger.info("Cleanup successful.")
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed: {cleanup_error}")
            return

    logger.info("Organization setup completed successfully!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup a new Auth0 Organization")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without making changes"
    )

    args = parser.parse_args()

    print("--- Auth0 Organization Setup ---")

    # Interactive prompts
    try:
        org_name = input("Organization Name (slug, e.g., my-org): ").strip()
        if not org_name:
            logger.error("Organization Name is required.")
            return

        display_name = input("Display Name (e.g., My Organization): ").strip()
        if not display_name:
            logger.error("Display Name is required.")
            return

        admin_email = input("Admin Email: ").strip()
        if not admin_email:
            logger.error("Admin Email is required.")
            return

        print("\nReview Configuration:")
        print(f"  Organization Name: {org_name}")
        print(f"  Display Name:      {display_name}")
        print(f"  Admin Email:       {admin_email}")
        print(f"  Dry Run:           {args.dry_run}")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        setup_org(org_name, display_name, admin_email, args.dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return


if __name__ == "__main__":
    main()
