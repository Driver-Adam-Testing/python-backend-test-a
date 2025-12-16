import argparse
import logging

from database.models import BillingFrequency, PlanType
from shared.usage.utils import sloc_to_bytes

from tools.org_setup.config import (
    DEFAULT_SLOC_CREDITS,
    SUPPORT_EMAIL,
    CreditsConfig,
    OrgSetupConfig,
)

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auth0 Organization Admin CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (run from backend directory):
  poetry run python -m tools.setup_org org                     # Create org with defaults
  poetry run python -m tools.setup_org credits                 # Issue credits to existing org
  poetry run python -m tools.setup_org org --dry-run           # Dry run org creation
  poetry run python -m tools.setup_org org --sloc 1000000      # Custom SLOC credits
  poetry run python -m tools.setup_org org --plan enterprise   # Enterprise plan
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
        default=DEFAULT_SLOC_CREDITS,
        help=f"Initial SLOC credits (default: {DEFAULT_SLOC_CREDITS:,})",
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

    return parser


def prompt_for_org_config(
    sloc_credits: int, plan: str, billing: str
) -> OrgSetupConfig | None:
    print("--- Auth0 Organization Setup ---")
    print(f"Note: {SUPPORT_EMAIL} will be auto-included as admin.\n")

    try:
        org_name = _prompt_required(
            "Organization Name (slug, e.g., my-org): ",
            "Organization Name is required.",
        )
        if not org_name:
            return None

        display_name = _prompt_required(
            "Display Name (e.g., My Organization): ",
            "Display Name is required.",
        )
        if not display_name:
            return None

        admin_input = input(
            "Admin Emails (comma-separated, or press Enter for support only): "
        ).strip()
        admin_emails = [e.strip().lower() for e in admin_input.split(",") if e.strip()]

        try:
            config = OrgSetupConfig(
                org_name=org_name,
                display_name=display_name,
                admin_emails=admin_emails,
                plan_type=PlanType(plan),
                billing_frequency=BillingFrequency(billing),
                sloc_credits=sloc_credits,
            )
        except ValueError as e:
            logger.error(str(e))
            return None

        _display_org_config(config)

        if not _confirm("Proceed?"):
            print("Aborted.")
            return None

        return config

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return None


def prompt_for_credits_config() -> CreditsConfig | None:
    print("--- Issue Usage Credits ---")
    print("Note: Credits are entered in SLOC (1 SLOC = 50 bytes)\n")

    try:
        organization_id = _prompt_required(
            "Organization ID (e.g., org_xxx): ",
            "Organization ID is required.",
        )
        if not organization_id:
            return None

        sloc_amount = _prompt_positive_int(
            "Credit Amount in SLOC (integer): ", "Credit Amount"
        )
        if not sloc_amount:
            return None

        config = CreditsConfig(organization_id=organization_id, sloc_amount=sloc_amount)

        _display_credits_config(config)

        if not _confirm("Proceed?"):
            print("Aborted.")
            return None

        return config

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return None


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


def _confirm(prompt: str) -> bool:
    response = input(f"\n{prompt} (y/N): ").strip().lower()
    return response == "y"


def _display_org_config(config: OrgSetupConfig) -> None:
    print("\nReview Configuration:")
    print(f"  Organization Name:  {config.org_name}")
    print(f"  Display Name:       {config.display_name}")
    print(f"  Admin Emails:       {', '.join(config.admin_emails_with_support)}")
    print(f"  Plan:               {config.plan_type.value}")
    print(f"  Billing:            {config.billing_frequency.value}")
    print(f"  Initial Credits:    {config.sloc_credits:,} SLOC")


def _display_credits_config(config: CreditsConfig) -> None:
    bytes_amount = sloc_to_bytes(config.sloc_amount)
    print("\nReview Configuration:")
    print(f"  Organization ID:  {config.organization_id}")
    print(f"  Issued By:        {config.user_id}")
    print(f"  Credit Amount:    {config.sloc_amount:,} SLOC ({bytes_amount:,} bytes)")
    print("  Credit Type:      BASE_PLATFORM_USAGE_CREDIT")
