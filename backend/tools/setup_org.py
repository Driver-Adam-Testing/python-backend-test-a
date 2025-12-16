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
    poetry run python -m tools.setup_org org
    poetry run python -m tools.setup_org credits
    poetry run python -m tools.setup_org org --dry-run
    poetry run python -m tools.setup_org org --sloc 1000000 --plan enterprise --billing annual
"""

import logging
import sys

from app.services.auth0_factory import create_auth0_service
from auth0.exceptions import Auth0Error
from database.db import get_session

from tools.org_setup.cli import (
    create_parser,
    prompt_for_credits_config,
    prompt_for_org_config,
)
from tools.org_setup.exceptions import OrgSetupError
from tools.org_setup.service import CreditsService, OrgSetupService

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_org_command(dry_run: bool, sloc: int, plan: str, billing: str) -> int:
    config = prompt_for_org_config(sloc, plan, billing)
    if not config:
        return 1

    print(f"  Dry Run:            {dry_run}")

    try:
        auth0_service = create_auth0_service()
    except Auth0Error as e:
        logger.error(f"Failed to initialize Auth0Service: {e}")
        return 1

    service = OrgSetupService(
        auth0_service=auth0_service,
        session_factory=get_session,
        dry_run=dry_run,
    )

    try:
        org_id = service.setup(config)
        logger.info(f"Organization ID: {org_id}")
        return 0
    except OrgSetupError as e:
        logger.error(str(e))
        return 1


def run_credits_command(dry_run: bool) -> int:
    config = prompt_for_credits_config()
    if not config:
        return 1

    print(f"  Dry Run:          {dry_run}")

    service = CreditsService(session_factory=get_session, dry_run=dry_run)

    try:
        service.issue_credits(
            config.organization_id, config.user_id, config.sloc_amount
        )
        return 0
    except OrgSetupError as e:
        logger.error(str(e))
        return 1


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "org":
        return run_org_command(args.dry_run, args.sloc, args.plan, args.billing)
    elif args.command == "credits":
        return run_credits_command(args.dry_run)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
