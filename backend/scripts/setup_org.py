#!/usr/bin/env python3
"""
Auth0 Organization Admin CLI

Creates and manages Auth0 organizations with all required components.

Commands:
    org      Create org with admins, subscription (Advanced), and 250k SLOC credits
    credits  Issue additional SLOC credits to an existing organization

Required Environment Variables:
    AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_MGMT_API_DOMAIN,
    AUTH0_MGMT_API_CLIENT_ID, AUTH0_MGMT_API_CLIENT_SECRET

    DATABASE_URL (or individual: POSTGRES_SERVER, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)

Usage:
    poetry run python scripts/setup_org.py org             # Create org
    poetry run python scripts/setup_org.py credits         # Issue credits
    poetry run python scripts/setup_org.py org --dry-run   # Simulate
"""

import argparse
import logging
import os
import re
import sys
from typing import Any

# Add backend dir to path so 'app' module is importable when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.auth0_factory import Auth0Service, create_auth0_service
from auth0.exceptions import Auth0Error
from database.db import get_session
from database.models import BillingFrequency, PlanType, UsageEventType
from shared.billing.billing_service import BillingService
from shared.usage.usage_service import UsageService
from shared.usage.utils import sloc_to_bytes
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SUPPORT_EMAIL = "support@driverai.com"
INITIAL_SLOC_CREDITS = 250_000
SYSTEM_USER_ID = "SYSTEM"
ORG_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def validate_org_name(name: str) -> bool:
    return bool(ORG_NAME_PATTERN.match(name))


def _prompt_required(prompt: str, error_msg: str) -> str | None:
    value = input(prompt).strip()
    if not value:
        logger.error(error_msg)
        return None
    return value


def _prompt_positive_int(prompt: str, field_name: str) -> int | None:
    value = input(prompt).strip()
    if not value:
        logger.error(f"{field_name} is required.")
        return None
    try:
        num = int(value)
        if num <= 0:
            logger.error(f"{field_name} must be a positive integer.")
            return None
        return num
    except ValueError:
        logger.error(f"{field_name} must be a valid integer.")
        return None


def _cleanup_org(service: Auth0Service, org_id: str) -> None:
    try:
        logger.info(f"Cleaning up organization {org_id}...")
        service.delete_organization(org_id)
        logger.info("Cleanup successful.")
    except Auth0Error as e:
        logger.error(f"Cleanup failed: {e}")


def _create_auth0_org(
    service: Auth0Service, org_name: str, display_name: str
) -> dict[str, Any] | None:
    try:
        org = service.create_organization(
            name=org_name,
            display_name=display_name,
            metadata={"self_service": "false"},
        )
        logger.info(f"Created organization: {org['id']}")
        return org
    except Auth0Error as e:
        logger.error(f"Failed to create organization: {e}")
        return None


def _enable_connection(service: Auth0Service, org_id: str) -> bool:
    try:
        conn_id = service.get_username_password_connection_id()
        service.enable_connection_for_organization(org_id=org_id, connection_id=conn_id)
        logger.info("Enabled Username-Password-Authentication connection")
        return True
    except Auth0Error as e:
        logger.error(f"Failed to enable connection: {e}")
        return False


def _invite_admins(service: Auth0Service, org_id: str, admin_emails: list[str]) -> bool:
    role_name = "org_super_admin"
    for email in admin_emails:
        try:
            service.create_admin_invite(org_id=org_id, email=email, role_name=role_name)
            logger.info(f"Invited {email} with role '{role_name}'")
        except Auth0Error as e:
            logger.error(f"Failed to invite {email}: {e}")
            return False
    return True


def _create_subscription(org_id: str) -> bool:
    try:
        with get_session() as session:
            subscription = BillingService(session).create_subscription(
                organization_id=org_id,
                plan_type=PlanType.ADVANCED,
                billing_frequency=BillingFrequency.NEVER,
            )
            logger.info(f"Created subscription: {subscription.id}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create subscription: {e}")
        return False


def _issue_initial_credits(org_id: str, sloc_amount: int) -> bool:
    bytes_amount = sloc_to_bytes(sloc_amount)
    try:
        with get_session() as session:
            UsageService(session).issue_usage_credits(
                organization_id=org_id,
                user_id=SYSTEM_USER_ID,
                event_type=UsageEventType.BASE_PLATFORM_USAGE_CREDIT,
                credit_amount=bytes_amount,
            )
            logger.info(f"Issued {sloc_amount:,} SLOC credits")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to issue credits: {e}")
        return False


def _log_dry_run_steps(org_id: str, admin_emails: list[str]) -> None:
    logger.info("[DRY RUN] Would initialize Auth0Service")
    logger.info(f"[DRY RUN] Would enable connection for org {org_id}")
    for email in admin_emails:
        logger.info(f"[DRY RUN] Would invite '{email}' with role 'org_super_admin'")
    logger.info(f"[DRY RUN] Would create Advanced subscription for org {org_id}")
    bytes_amount = sloc_to_bytes(INITIAL_SLOC_CREDITS)
    logger.info(
        f"[DRY RUN] Would issue {INITIAL_SLOC_CREDITS:,} SLOC ({bytes_amount:,} bytes)"
    )


def setup_org(
    org_name: str, display_name: str, admin_emails: list[str], dry_run: bool = False
) -> None:
    """
    1. Create the organization
    2. Enable Username-Password-Authentication connection
    3. Invite all admin emails with org_super_admin role
    4. Create Advanced subscription
    5. Issue initial SLOC credits
    """
    logger.info(f"Starting organization setup for '{display_name}' ({org_name})")
    logger.info(f"Admin Emails: {', '.join(admin_emails)}")

    if not validate_org_name(org_name):
        logger.error(
            f"Invalid organization name '{org_name}'. "
            "Must start with lowercase letter/digit and contain only lowercase letters, digits, hyphens, underscores."
        )
        return

    if dry_run:
        _log_dry_run_steps("org_mock_id", admin_emails)
        logger.info("Organization setup completed successfully!")
        return

    try:
        service = create_auth0_service()
    except Auth0Error as e:
        logger.error(f"Failed to initialize Auth0Service: {e}")
        return

    org = _create_auth0_org(service, org_name, display_name)
    if not org:
        return

    org_id = org["id"]

    def cleanup() -> None:
        _cleanup_org(service, org_id)

    if not _enable_connection(service, org_id):
        cleanup()
        return

    if not _invite_admins(service, org_id, admin_emails):
        cleanup()
        return

    if not _create_subscription(org_id):
        cleanup()
        return

    if not _issue_initial_credits(org_id, INITIAL_SLOC_CREDITS):
        cleanup()
        return

    logger.info("Organization setup completed successfully!")


def issue_credits(
    organization_id: str,
    user_id: str,
    sloc_amount: int,
    dry_run: bool = False,
) -> None:
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
            UsageService(session).issue_usage_credits(
                organization_id=organization_id,
                user_id=user_id,
                event_type=UsageEventType.BASE_PLATFORM_USAGE_CREDIT,
                credit_amount=bytes_amount,
            )
            logger.info(
                f"Successfully issued {sloc_amount} SLOC ({bytes_amount} bytes)!"
            )
            logger.info("Credit issuance completed successfully!")
    except SQLAlchemyError as e:
        logger.error(f"Failed to issue credits: {e}")


def run_org_command(dry_run: bool) -> None:
    print("--- Auth0 Organization Setup ---")
    print(f"Note: {SUPPORT_EMAIL} will be auto-included as admin.\n")

    try:
        org_name = _prompt_required(
            "Organization Name (slug, e.g., my-org): ", "Organization Name is required."
        )
        if not org_name:
            return

        if not validate_org_name(org_name):
            logger.error(
                "Invalid organization name. Must start with lowercase letter/digit "
                "and contain only lowercase letters, digits, hyphens, underscores."
            )
            return

        display_name = _prompt_required(
            "Display Name (e.g., My Organization): ", "Display Name is required."
        )
        if not display_name:
            return

        admin_input = input(
            "Admin Emails (comma-separated, or press Enter for support only): "
        ).strip()
        raw_emails = [e.strip().lower() for e in admin_input.split(",") if e.strip()]
        admin_emails = list(dict.fromkeys([SUPPORT_EMAIL, *raw_emails]))

        print("\nReview Configuration:")
        print(f"  Organization Name:  {org_name}")
        print(f"  Display Name:       {display_name}")
        print(f"  Admin Emails:       {', '.join(admin_emails)}")
        print("  Plan:               Advanced")
        print(f"  Initial Credits:    {INITIAL_SLOC_CREDITS:,} SLOC")
        print(f"  Dry Run:            {dry_run}")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        setup_org(org_name, display_name, admin_emails, dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")


def run_credits_command(dry_run: bool) -> None:
    print("--- Issue Usage Credits ---")
    print("Note: Credits are entered in SLOC (1 SLOC = 50 bytes)\n")

    try:
        organization_id = _prompt_required(
            "Organization ID (e.g., org_xxx): ", "Organization ID is required."
        )
        if not organization_id:
            return

        sloc_amount = _prompt_positive_int(
            "Credit Amount in SLOC (integer): ", "Credit Amount"
        )
        if not sloc_amount:
            return

        bytes_amount = sloc_to_bytes(sloc_amount)

        print("\nReview Configuration:")
        print(f"  Organization ID:  {organization_id}")
        print(f"  Issued By:        {SUPPORT_EMAIL}")
        print(f"  Credit Amount:    {sloc_amount:,} SLOC ({bytes_amount:,} bytes)")
        print("  Credit Type:      BASE_PLATFORM_USAGE_CREDIT")
        print(f"  Dry Run:          {dry_run}")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        issue_credits(organization_id, SUPPORT_EMAIL, sloc_amount, dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auth0 Organization Admin CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_org.py org             # Create org with subscription + credits
  python scripts/setup_org.py credits         # Issue additional credits to existing org
  python scripts/setup_org.py org --dry-run   # Dry run organization creation
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    org_parser = subparsers.add_parser(
        "org", help="Create Auth0 org with admins, subscription, and initial credits"
    )
    org_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without making changes"
    )

    credits_parser = subparsers.add_parser(
        "credits", help="Issue additional SLOC credits to an existing organization"
    )
    credits_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without making changes"
    )

    args = parser.parse_args()

    if args.command == "org":
        run_org_command(args.dry_run)
    elif args.command == "credits":
        run_credits_command(args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
