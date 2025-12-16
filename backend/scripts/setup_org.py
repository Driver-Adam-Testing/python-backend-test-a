#!/usr/bin/env python3
"""
Auth0 Organization Admin CLI

Creates and manages Auth0 organizations with all required components.

Commands:
    org      Create org with admins, subscription, and SLOC credits
    credits  Issue additional SLOC credits to an existing organization

Required Environment Variables:
    AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_MGMT_API_DOMAIN,
    AUTH0_MGMT_API_CLIENT_ID, AUTH0_MGMT_API_CLIENT_SECRET

    DATABASE_URL (or individual: POSTGRES_SERVER, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)

Usage (run from the backend directory):
    poetry run python -m scripts.setup_org org
    poetry run python -m scripts.setup_org credits
    poetry run python -m scripts.setup_org org --dry-run
    poetry run python -m scripts.setup_org org --sloc 1000000 --plan enterprise --billing annual
"""

import argparse
import logging
import os
import re
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.auth0_factory import Auth0Service, create_auth0_service
from auth0.exceptions import Auth0Error
from database.db import get_session
from database.models import (
    BillingFrequency,
    Organization,
    OrgMembership,
    PlanType,
    UsageEventType,
    User,
)
from database.models_enums import OrgRole
from shared.billing.billing_service import BillingService
from shared.usage.usage_service import UsageService
from shared.usage.utils import sloc_to_bytes
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SUPPORT_EMAIL = "support@driverai.com"
SUPPORT_NAME = "Driver Support"
INITIAL_SLOC_CREDITS = 500_000
SYSTEM_USER_ID = "SYSTEM"
ORG_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

# Password generation constants
PASSWORD_LENGTH = 16
PASSWORD_SPECIAL_CHARS = "!@#$%^&*"


def _generate_password() -> str:
    """
    Auth0 password requirements:
    - At least 8 characters (we use 16)
    - Lower case (a-z), upper case (A-Z), and numbers (0-9)
    - Special characters (!@#$%^&*)
    - No more than 2 identical characters in a row
    """
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = PASSWORD_SPECIAL_CHARS

    # Ensure at least one of each required character type
    password_chars = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    # Fill remaining characters
    all_chars = lowercase + uppercase + digits + special
    remaining_length = PASSWORD_LENGTH - len(password_chars)
    for _ in range(remaining_length):
        password_chars.append(secrets.choice(all_chars))

    # Shuffle to randomize positions
    secrets.SystemRandom().shuffle(password_chars)
    password = "".join(password_chars)

    # Ensure no more than 2 identical characters in a row
    password = _fix_consecutive_chars(password, all_chars)

    return password


def _fix_consecutive_chars(password: str, all_chars: str) -> str:
    """Ensure no more than 2 identical consecutive characters."""
    result = list(password)
    for i in range(2, len(result)):
        if result[i] == result[i - 1] == result[i - 2]:
            # Find a different character
            for char in all_chars:
                if char != result[i]:
                    result[i] = char
                    break
    return "".join(result)


def _get_downloads_dir() -> Path:
    """Get the user's Downloads directory."""
    home = Path.home()
    downloads = home / "Downloads"
    if downloads.exists():
        return downloads
    # Fallback to home directory if Downloads doesn't exist
    return home


def _save_credentials_file(org_name: str, email: str, password: str) -> Path:
    """Save credentials to a file in the Downloads directory."""
    downloads_dir = _get_downloads_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"driver_support_credentials_{org_name}_{timestamp}.txt"
    filepath = downloads_dir / filename

    content = f"""Driver Support Account Credentials
==================================

Organization: {org_name}
Email:        {email}
Password:     {password}

Created:      {datetime.now().isoformat()}

⚠️  IMPORTANT: Save this password securely - it will not be shown again.
⚠️  This file should be deleted after the password is stored securely.
"""

    filepath.write_text(content)
    # Set file permissions to owner-only read/write (Unix)
    try:
        os.chmod(filepath, 0o600)
    except OSError:
        pass  # Windows doesn't support chmod the same way

    return filepath


def _create_db_organization(org_id: str, name: str, display_name: str) -> bool:
    try:
        with get_session() as session:
            org = Organization(
                id=org_id,
                name=name,
                display_name=display_name,
                org_metadata={"self_service": "false"},
                auth0_updated_at=datetime.now(),
            )
            session.add(org)
            session.commit()
            logger.info(f"Created DB organization record for {org_id}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create DB organization: {e}")
        return False


def _ensure_db_user_exists(user_id: str, email: str, name: str | None = None) -> bool:
    try:
        with get_session() as session:
            existing = session.get(User, user_id)
            if existing:
                logger.info(f"User {user_id} already exists in DB")
                return True

            user = User(
                id=user_id,
                email=email,
                name=name,
                auth0_updated_at=datetime.now(),
            )
            session.add(user)
            session.commit()
            logger.info(f"Created DB user record for {user_id}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create DB user: {e}")
        return False


def _create_db_membership(org_id: str, user_id: str, role: OrgRole) -> bool:
    try:
        with get_session() as session:
            membership = OrgMembership(org_id=org_id, user_id=user_id, role=role)
            session.add(membership)
            session.commit()
            logger.info(
                f"Created DB membership for {user_id} in {org_id} with role {role.value}"
            )
            return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create DB membership: {e}")
        return False


def _setup_support_account(service: Auth0Service, org_id: str, org_name: str) -> bool:
    """
    Set up the support account for an organization.

    For existing tenants (dev/stage/prod): Adds existing support user directly.
    For single-tenant deployments: Creates support user if needed, saves credentials.
    """
    try:
        # Check if support user exists in Auth0
        existing_users = service.find_users_by_email(SUPPORT_EMAIL)

        if existing_users:
            user_id = existing_users[0]["user_id"]
            logger.info(f"Found existing support user: {user_id}")
        else:
            # Single-tenant scenario: Create the support user
            logger.info(
                "Support user not found, creating new user for single-tenant..."
            )
            password = _generate_password()

            user_data = service.create_user(
                email=SUPPORT_EMAIL,
                password=password,
                name=SUPPORT_NAME,
            )
            user_id = user_data["user_id"]
            logger.info(f"Created support user: {user_id}")

            # Save credentials to file
            filepath = _save_credentials_file(org_name, SUPPORT_EMAIL, password)
            logger.info(f"⚠️  Support credentials saved to: {filepath}")
            print(f"\n{'='*60}")
            print("⚠️  NEW SUPPORT USER CREATED")
            print(f"⚠️  Credentials saved to: {filepath}")
            print("⚠️  Please store the password securely and delete the file.")
            print(f"{'='*60}\n")

        # Add support user to organization
        service.add_organization_members(org_id, [user_id])
        logger.info(f"Added support user to organization {org_id}")

        # Assign Admin role in Auth0
        admin_role_id = service.get_admin_role_id()
        service.assign_organization_member_roles(org_id, user_id, [admin_role_id])
        logger.info("Assigned Admin role to support user")

        # Ensure user exists in DB (required for foreign key constraint)
        if not _ensure_db_user_exists(user_id, SUPPORT_EMAIL, SUPPORT_NAME):
            return False

        # Create DB membership
        if not _create_db_membership(org_id, user_id, OrgRole.org_super_admin):
            return False

        return True

    except (Auth0Error, SQLAlchemyError) as e:
        logger.error(f"Failed to setup support account: {e}")
        return False


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


def _create_subscription(
    org_id: str, plan_type: PlanType, billing_frequency: BillingFrequency
) -> bool:
    try:
        with get_session() as session:
            subscription = BillingService(session).create_subscription(
                organization_id=org_id,
                plan_type=plan_type,
                billing_frequency=billing_frequency,
            )
            logger.info(
                f"Created subscription: {subscription.id} ({plan_type.value}, {billing_frequency.value})"
            )
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


def _log_dry_run_steps(
    org_id: str,
    admin_emails: list[str],
    plan_type: PlanType,
    billing_frequency: BillingFrequency,
    sloc_amount: int,
) -> None:
    logger.info("[DRY RUN] Would initialize Auth0Service")
    logger.info(f"[DRY RUN] Would enable connection for org {org_id}")
    logger.info(
        f"[DRY RUN] Would setup support account ({SUPPORT_EMAIL}) - create if needed, add to org, assign Admin role"
    )
    other_admins = [e for e in admin_emails if e != SUPPORT_EMAIL]
    for email in other_admins:
        logger.info(f"[DRY RUN] Would invite '{email}' with role 'org_super_admin'")
    logger.info(
        f"[DRY RUN] Would create {plan_type.value} subscription ({billing_frequency.value}) for org {org_id}"
    )
    bytes_amount = sloc_to_bytes(sloc_amount)
    logger.info(f"[DRY RUN] Would issue {sloc_amount:,} SLOC ({bytes_amount:,} bytes)")


def setup_org(
    org_name: str,
    display_name: str,
    admin_emails: list[str],
    plan_type: PlanType,
    billing_frequency: BillingFrequency,
    sloc_credits: int,
    dry_run: bool = False,
) -> None:
    """
    1. Create the organization
    2. Enable Username-Password-Authentication connection
    3. Setup support account (create if needed, add directly to org)
    4. Invite other admin emails with org_super_admin role
    5. Create subscription with specified plan and billing
    6. Issue initial SLOC credits
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
        _log_dry_run_steps(
            "org_mock_id", admin_emails, plan_type, billing_frequency, sloc_credits
        )
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

    # Create organization in local DB (required for foreign key constraints)
    if not _create_db_organization(org_id, org_name, display_name):
        cleanup()
        return

    if not _enable_connection(service, org_id):
        cleanup()
        return

    # Setup support account (create if needed, add directly to org with Admin role)
    if not _setup_support_account(service, org_id, org_name):
        cleanup()
        return

    # Invite other admin emails (not support - that was handled above)
    other_admin_emails = [e for e in admin_emails if e != SUPPORT_EMAIL]
    if other_admin_emails and not _invite_admins(service, org_id, other_admin_emails):
        cleanup()
        return

    if not _create_subscription(org_id, plan_type, billing_frequency):
        cleanup()
        return

    if not _issue_initial_credits(org_id, sloc_credits):
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


def run_org_command(
    dry_run: bool,
    sloc_credits: int,
    plan: str,
    billing: str,
) -> None:
    plan_type = PlanType(plan)
    billing_frequency = BillingFrequency(billing)

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
        print(f"  Plan:               {plan_type.value}")
        print(f"  Billing:            {billing_frequency.value}")
        print(f"  Initial Credits:    {sloc_credits:,} SLOC")
        print(f"  Dry Run:            {dry_run}")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

        setup_org(
            org_name,
            display_name,
            admin_emails,
            plan_type,
            billing_frequency,
            sloc_credits,
            dry_run,
        )

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
Examples (run from backend directory):
  poetry run python -m scripts.setup_org org                     # Create org with defaults
  poetry run python -m scripts.setup_org credits                 # Issue credits to existing org
  poetry run python -m scripts.setup_org org --dry-run           # Dry run org creation
  poetry run python -m scripts.setup_org org --sloc 1000000      # Custom SLOC credits
  poetry run python -m scripts.setup_org org --plan enterprise   # Enterprise plan
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    org_parser = subparsers.add_parser(
        "org", help="Create Auth0 org with admins, subscription, and initial credits"
    )
    org_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without making changes"
    )
    org_parser.add_argument(
        "--sloc",
        type=int,
        default=INITIAL_SLOC_CREDITS,
        help=f"Initial SLOC credits (default: {INITIAL_SLOC_CREDITS:,})",
    )
    org_parser.add_argument(
        "--plan",
        type=str,
        choices=["free", "core", "advanced", "enterprise"],
        default="advanced",
        help="Subscription plan type (default: advanced)",
    )
    org_parser.add_argument(
        "--billing",
        type=str,
        choices=["never", "monthly", "annual"],
        default="annual",
        help="Billing frequency (default: annual)",
    )

    credits_parser = subparsers.add_parser(
        "credits", help="Issue additional SLOC credits to an existing organization"
    )
    credits_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without making changes"
    )

    args = parser.parse_args()

    if args.command == "org":
        run_org_command(args.dry_run, args.sloc, args.plan, args.billing)
    elif args.command == "credits":
        run_credits_command(args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
