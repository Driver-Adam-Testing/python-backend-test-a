#!/usr/bin/env python3
"""
Auth0 Organization Admin CLI

This script provides administrative commands for managing Auth0 organizations,
subscriptions, and usage credits.

Usage:
    python scripts/setup_org.py org                    # Create a new organization
    python scripts/setup_org.py subscription           # Create a subscription
    python scripts/setup_org.py credits                # Issue usage credits

    Add --dry-run to any command to simulate without making changes.
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

# We need to add 'driver_db' to path to import 'database'
# backend/scripts/ -> ../../driver_db
sys.path.append(os.path.join(os.path.dirname(__file__), "../../driver_db"))

from app.services.auth0_factory import create_auth0_service
from database.db import get_session
from database.models import BillingFrequency, PlanType, UsageEventType
from shared.billing.billing_service import BillingService
from shared.usage.usage_service import UsageService
from shared.usage.utils import sloc_to_bytes

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


def setup_subscription(
    organization_id: str,
    plan_type: PlanType,
    billing_frequency: BillingFrequency,
    dry_run: bool = False,
) -> None:
    """
    Creates a subscription for an organization.
    """
    logger.info(f"Starting subscription setup for organization '{organization_id}'")
    logger.info(f"Plan Type: {plan_type.value}")
    logger.info(f"Billing Frequency: {billing_frequency.value}")

    if dry_run:
        logger.info(
            f"[DRY RUN] Would create subscription: org='{organization_id}', "
            f"plan='{plan_type.value}', frequency='{billing_frequency.value}'"
        )
        logger.info("Subscription setup simulation completed!")
        return

    try:
        with get_session() as session:
            billing_service = BillingService(session)
            subscription = billing_service.create_subscription(
                organization_id=organization_id,
                plan_type=plan_type,
                billing_frequency=billing_frequency,
            )
            logger.info(f"Successfully created subscription: {subscription.id}")
            logger.info("Subscription setup completed successfully!")
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")


def issue_credits(
    organization_id: str,
    user_id: str,
    sloc_amount: int,
    dry_run: bool = False,
) -> None:
    """
    Issues usage credits to an organization.
    Credits are entered in SLOC and converted to bytes internally (1 SLOC = 50 bytes).
    """
    bytes_amount = sloc_to_bytes(sloc_amount)

    logger.info(f"Issuing credits to organization '{organization_id}'")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Credit Amount: {sloc_amount} SLOC ({bytes_amount} bytes)")

    if dry_run:
        logger.info(
            f"[DRY RUN] Would issue {sloc_amount} SLOC ({bytes_amount} bytes) "
            f"to org '{organization_id}' as BASE_PLATFORM_USAGE_CREDIT"
        )
        logger.info("Credit issuance simulation completed!")
        return

    try:
        with get_session() as session:
            usage_service = UsageService(session)
            usage_service.issue_usage_credits(
                organization_id=organization_id,
                user_id=user_id,
                event_type=UsageEventType.BASE_PLATFORM_USAGE_CREDIT,
                credit_amount=bytes_amount,
            )
            logger.info(
                f"Successfully issued {sloc_amount} SLOC ({bytes_amount} bytes)!"
            )
            logger.info("Credit issuance completed successfully!")
    except Exception as e:
        logger.error(f"Failed to issue credits: {e}")


def run_org_command(dry_run: bool) -> None:
    """Interactive prompts for organization setup."""
    print("--- Auth0 Organization Setup ---")

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
        print(f"  Dry Run:           {dry_run}")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        setup_org(org_name, display_name, admin_email, dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")


def run_subscription_command(dry_run: bool) -> None:
    """Interactive prompts for subscription setup."""
    print("--- Subscription Setup ---")

    plan_options = [p.value for p in PlanType]
    frequency_options = [f.value for f in BillingFrequency]

    try:
        organization_id = input("Organization ID (e.g., org_xxx): ").strip()
        if not organization_id:
            logger.error("Organization ID is required.")
            return

        print(f"\nAvailable Plan Types: {', '.join(plan_options)}")
        plan_input = input("Plan Type: ").strip().lower()
        if plan_input not in plan_options:
            logger.error(
                f"Invalid plan type. Must be one of: {', '.join(plan_options)}"
            )
            return
        plan_type = PlanType(plan_input)

        print(f"\nAvailable Billing Frequencies: {', '.join(frequency_options)}")
        freq_input = input("Billing Frequency: ").strip().lower()
        if freq_input not in frequency_options:
            logger.error(
                f"Invalid billing frequency. Must be one of: {', '.join(frequency_options)}"
            )
            return
        billing_frequency = BillingFrequency(freq_input)

        print("\nReview Configuration:")
        print(f"  Organization ID:    {organization_id}")
        print(f"  Plan Type:          {plan_type.value}")
        print(f"  Billing Frequency:  {billing_frequency.value}")
        print(f"  Dry Run:            {dry_run}")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        setup_subscription(organization_id, plan_type, billing_frequency, dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")


def run_credits_command(dry_run: bool) -> None:
    """Interactive prompts for issuing credits."""
    print("--- Issue Usage Credits ---")
    print("Note: Credits are entered in SLOC (1 SLOC = 50 bytes)")

    try:
        organization_id = input("\nOrganization ID (e.g., org_xxx): ").strip()
        if not organization_id:
            logger.error("Organization ID is required.")
            return

        user_id = input("Admin User ID (performing this action): ").strip()
        if not user_id:
            logger.error("User ID is required.")
            return

        sloc_input = input("Credit Amount in SLOC (integer): ").strip()
        if not sloc_input:
            logger.error("Credit Amount is required.")
            return
        try:
            sloc_amount = int(sloc_input)
            if sloc_amount <= 0:
                logger.error("Credit Amount must be a positive integer.")
                return
        except ValueError:
            logger.error("Credit Amount must be a valid integer.")
            return

        bytes_amount = sloc_to_bytes(sloc_amount)

        print("\nReview Configuration:")
        print(f"  Organization ID:  {organization_id}")
        print(f"  User ID:          {user_id}")
        print(f"  Credit Amount:    {sloc_amount} SLOC ({bytes_amount} bytes)")
        print("  Credit Type:      BASE_PLATFORM_USAGE_CREDIT")
        print(f"  Dry Run:          {dry_run}")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        issue_credits(organization_id, user_id, sloc_amount, dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auth0 Organization Admin CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_org.py org                    # Create a new organization
  python scripts/setup_org.py subscription           # Create a subscription
  python scripts/setup_org.py credits                # Issue usage credits
  python scripts/setup_org.py org --dry-run          # Dry run organization creation
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # org subcommand
    org_parser = subparsers.add_parser(
        "org", help="Create a new Auth0 organization with admin invite"
    )
    org_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without making changes"
    )

    # subscription subcommand
    sub_parser = subparsers.add_parser(
        "subscription", help="Create a subscription for an organization"
    )
    sub_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without making changes"
    )

    # credits subcommand
    credits_parser = subparsers.add_parser(
        "credits", help="Issue usage credits to an organization"
    )
    credits_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without making changes"
    )

    args = parser.parse_args()

    if args.command == "org":
        run_org_command(args.dry_run)
    elif args.command == "subscription":
        run_subscription_command(args.dry_run)
    elif args.command == "credits":
        run_credits_command(args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
