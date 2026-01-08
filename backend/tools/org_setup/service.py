import logging
import os
import secrets
import string
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.services.auth0_factory import Auth0Service
from auth0.exceptions import Auth0Error
from database.models import Organization, OrgMembership, UsageEventType, User
from database.models_enums import OrgRole
from shared.billing.billing_service import BillingService
from shared.usage.usage_service import UsageService
from shared.usage.utils import sloc_to_bytes
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from tools.org_setup.config import (
    SUPPORT_EMAIL,
    SUPPORT_NAME,
    SYSTEM_USER_ID,
    OrgSetupConfig,
)
from tools.org_setup.exceptions import (
    Auth0SetupError,
    DatabaseSetupError,
    RollbackError,
)

logger = logging.getLogger(__name__)

PASSWORD_LENGTH = 16
PASSWORD_SPECIAL_CHARS = "!@#$%^&*"

# Retry configuration for Auth0 API calls
AUTH0_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Auth0Error),
    reraise=True,
)


@dataclass
class SetupState:
    """Tracks created resources for potential rollback."""

    auth0_org_id: str | None = None
    db_org_created: bool = False
    support_user_id: str | None = None
    support_user_created: bool = False
    db_memberships: list[tuple[str, str]] = field(default_factory=list)
    subscription_created: bool = False
    credits_issued: bool = False


class OrgSetupService:
    """Orchestrates organization creation with rollback support."""

    def __init__(
        self,
        auth0_service: Auth0Service,
        session_factory: Callable[[], Session],
        dry_run: bool = False,
    ) -> None:
        self._auth0 = auth0_service
        self._session_factory = session_factory
        self._dry_run = dry_run
        self._state = SetupState()
        self._credentials_file: Path | None = None

    def setup(self, config: OrgSetupConfig) -> str:
        """
        Create organization with all components.

        Returns the Auth0 organization ID on success.
        Raises OrgSetupError on failure (after attempting rollback).
        """
        logger.info(
            f"Starting organization setup for '{config.display_name}' ({config.org_name})"
        )
        logger.info(f"Admin emails: {', '.join(config.admin_emails_with_support)}")

        if self._dry_run:
            self._log_dry_run(config)
            return "org_dry_run_mock"

        try:
            self._create_auth0_org(config)
            self._create_db_org(config)
            self._enable_connection()
            self._setup_support_account(config)
            self._invite_admins(config)
            self._create_subscription(config)
            self._issue_credits(config)

            logger.info("Organization setup completed successfully!")
            return self._state.auth0_org_id

        except (Auth0SetupError, DatabaseSetupError) as e:
            logger.error(f"Setup failed: {e}")
            self._rollback()
            raise

    @AUTH0_RETRY
    def _create_auth0_org(self, config: OrgSetupConfig) -> None:
        try:
            org = self._auth0.create_organization(
                name=config.org_name,
                display_name=config.display_name,
                metadata={"self_service": "false"},
            )
            self._state.auth0_org_id = org["id"]
            logger.info(f"Created Auth0 organization: {org['id']}")
        except Auth0Error as e:
            raise Auth0SetupError(f"Failed to create Auth0 organization: {e}") from e

    def _create_db_org(self, config: OrgSetupConfig) -> None:
        try:
            with self._session_factory() as session:
                org = Organization(
                    id=self._state.auth0_org_id,
                    name=config.org_name,
                    display_name=config.display_name,
                    org_metadata={"self_service": "false"},
                    auth0_updated_at=datetime.now(),
                )
                session.add(org)
                session.commit()
                self._state.db_org_created = True
                logger.info(
                    f"Created DB organization record: {self._state.auth0_org_id}"
                )
        except SQLAlchemyError as e:
            raise DatabaseSetupError(f"Failed to create DB organization: {e}") from e

    @AUTH0_RETRY
    def _enable_connection(self) -> None:
        try:
            conn_id = self._auth0.get_username_password_connection_id()
            self._auth0.enable_connection_for_organization(
                org_id=self._state.auth0_org_id,
                connection_id=conn_id,
            )
            logger.info("Enabled Username-Password-Authentication connection")
        except Auth0Error as e:
            raise Auth0SetupError(f"Failed to enable connection: {e}") from e

    def _setup_support_account(self, config: OrgSetupConfig) -> None:
        try:
            existing_users = self._auth0.find_users_by_email(SUPPORT_EMAIL)

            if existing_users:
                user_id = existing_users[0]["user_id"]
                logger.info(f"Found existing support user: {user_id}")
            else:
                user_id = self._create_support_user(config.org_name)

            self._state.support_user_id = user_id
            self._add_user_to_org(user_id, OrgRole.org_super_admin, is_support=True)

        except (Auth0Error, SQLAlchemyError) as e:
            raise Auth0SetupError(f"Failed to setup support account: {e}") from e

    @AUTH0_RETRY
    def _create_support_user(self, org_name: str) -> str:
        logger.info("Support user not found, creating new user...")
        password = _generate_password()

        user_data = self._auth0.create_user(
            email=SUPPORT_EMAIL,
            password=password,
            name=SUPPORT_NAME,
        )
        user_id = user_data["user_id"]
        self._state.support_user_created = True
        logger.info(f"Created support user: {user_id}")

        self._credentials_file = _save_credentials_file(
            org_name, SUPPORT_EMAIL, password
        )
        logger.info(f"Support credentials saved to: {self._credentials_file}")
        _print_credentials_warning(self._credentials_file)

        return user_id

    def _add_user_to_org(
        self, user_id: str, role: OrgRole, is_support: bool = False
    ) -> None:
        org_id = self._state.auth0_org_id

        self._auth0.add_organization_members(org_id, [user_id])
        logger.info(f"Added user {user_id} to organization")

        if role == OrgRole.org_super_admin:
            admin_role_id = self._auth0.get_admin_role_id()
            self._auth0.assign_organization_member_roles(
                org_id, user_id, [admin_role_id]
            )
            logger.info(f"Assigned Admin role to user {user_id}")

        self._ensure_db_user_exists(
            user_id,
            SUPPORT_EMAIL if is_support else user_id,
            SUPPORT_NAME if is_support else None,
        )
        self._create_db_membership(org_id, user_id, role)

    def _ensure_db_user_exists(
        self, user_id: str, email: str, name: str | None = None
    ) -> None:
        try:
            with self._session_factory() as session:
                existing = session.get(User, user_id)
                if existing:
                    logger.info(f"User {user_id} already exists in DB")
                    return

                user = User(
                    id=user_id,
                    email=email,
                    name=name,
                    auth0_updated_at=datetime.now(),
                )
                session.add(user)
                session.commit()
                logger.info(f"Created DB user record: {user_id}")
        except SQLAlchemyError as e:
            raise DatabaseSetupError(f"Failed to create DB user: {e}") from e

    def _create_db_membership(self, org_id: str, user_id: str, role: OrgRole) -> None:
        try:
            with self._session_factory() as session:
                membership = OrgMembership(org_id=org_id, user_id=user_id, role=role)
                session.add(membership)
                session.commit()
                self._state.db_memberships.append((org_id, user_id))
                logger.info(
                    f"Created DB membership: {user_id} in {org_id} with role {role.value}"
                )
        except SQLAlchemyError as e:
            raise DatabaseSetupError(f"Failed to create DB membership: {e}") from e

    def _invite_admins(self, config: OrgSetupConfig) -> None:
        role_name = "org_super_admin"
        for email in config.non_support_admin_emails:
            try:
                self._auth0.create_admin_invite(
                    org_id=self._state.auth0_org_id,
                    email=email,
                    role_name=role_name,
                )
                logger.info(f"Invited {email} with role '{role_name}'")
            except Auth0Error as e:
                raise Auth0SetupError(f"Failed to invite {email}: {e}") from e

    def _create_subscription(self, config: OrgSetupConfig) -> None:
        try:
            with self._session_factory() as session:
                subscription = BillingService(session).create_subscription(
                    organization_id=self._state.auth0_org_id,
                    plan_type=config.plan_type,
                    billing_frequency=config.billing_frequency,
                )
                self._state.subscription_created = True
                logger.info(
                    f"Created subscription: {subscription.id} "
                    f"({config.plan_type.value}, {config.billing_frequency.value})"
                )
        except SQLAlchemyError as e:
            raise DatabaseSetupError(f"Failed to create subscription: {e}") from e

    def _issue_credits(self, config: OrgSetupConfig) -> None:
        bytes_amount = sloc_to_bytes(config.sloc_credits)
        try:
            with self._session_factory() as session:
                UsageService(session).issue_usage_credits(
                    organization_id=self._state.auth0_org_id,
                    user_id=SYSTEM_USER_ID,
                    event_type=UsageEventType.BASE_PLATFORM_USAGE_CREDIT,
                    credit_amount=bytes_amount,
                )
                self._state.credits_issued = True
                logger.info(f"Issued {config.sloc_credits:,} SLOC credits")
        except SQLAlchemyError as e:
            raise DatabaseSetupError(f"Failed to issue credits: {e}") from e

    def _rollback(self) -> None:
        logger.info("Attempting rollback...")
        errors = []

        if self._state.auth0_org_id:
            try:
                self._auth0.delete_organization(self._state.auth0_org_id)
                logger.info(
                    f"Rolled back Auth0 organization: {self._state.auth0_org_id}"
                )
            except Auth0Error as e:
                errors.append(f"Failed to delete Auth0 org: {e}")

        # Note: DB records (org, memberships, subscription, credits) will be orphaned
        # if Auth0 org is deleted. In production, consider cascade deletes or
        # explicit DB cleanup here.

        if errors:
            logger.error(f"Rollback completed with errors: {errors}")
            raise RollbackError(f"Rollback had errors: {errors}")

        logger.info("Rollback completed successfully")

    def _log_dry_run(self, config: OrgSetupConfig) -> None:
        bytes_amount = sloc_to_bytes(config.sloc_credits)
        logger.info("[DRY RUN] Would create Auth0 organization")
        logger.info("[DRY RUN] Would create DB organization record")
        logger.info(
            "[DRY RUN] Would enable Username-Password-Authentication connection"
        )
        logger.info(f"[DRY RUN] Would setup support account ({SUPPORT_EMAIL})")
        for email in config.non_support_admin_emails:
            logger.info(f"[DRY RUN] Would invite '{email}' with role 'org_super_admin'")
        logger.info(
            f"[DRY RUN] Would create {config.plan_type.value} subscription "
            f"({config.billing_frequency.value})"
        )
        logger.info(
            f"[DRY RUN] Would issue {config.sloc_credits:,} SLOC ({bytes_amount:,} bytes)"
        )
        logger.info("Organization setup simulation completed!")


class CreditsService:
    """Issues credits to existing organizations."""

    def __init__(
        self, session_factory: Callable[[], Session], dry_run: bool = False
    ) -> None:
        self._session_factory = session_factory
        self._dry_run = dry_run

    def issue_credits(
        self, organization_id: str, user_id: str, sloc_amount: int
    ) -> None:
        bytes_amount = sloc_to_bytes(sloc_amount)

        logger.info(f"Issuing credits to organization '{organization_id}'")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Credit Amount: {sloc_amount:,} SLOC ({bytes_amount:,} bytes)")

        if self._dry_run:
            logger.info(
                f"[DRY RUN] Would issue {sloc_amount:,} SLOC ({bytes_amount:,} bytes) "
                f"to org '{organization_id}' as BASE_PLATFORM_USAGE_CREDIT"
            )
            logger.info("Credit issuance simulation completed!")
            return

        try:
            with self._session_factory() as session:
                UsageService(session).issue_usage_credits(
                    organization_id=organization_id,
                    user_id=user_id,
                    event_type=UsageEventType.BASE_PLATFORM_USAGE_CREDIT,
                    credit_amount=bytes_amount,
                )
                logger.info(
                    f"Successfully issued {sloc_amount:,} SLOC ({bytes_amount:,} bytes)!"
                )
                logger.info("Credit issuance completed successfully!")
        except SQLAlchemyError as e:
            raise DatabaseSetupError(f"Failed to issue credits: {e}") from e


def _generate_password() -> str:
    """
    Generate Auth0-compliant password:
    - At least 8 characters (we use 16)
    - Lower case, upper case, numbers, and special characters
    - No more than 2 identical characters in a row
    """
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = PASSWORD_SPECIAL_CHARS

    password_chars = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    all_chars = lowercase + uppercase + digits + special
    for _ in range(PASSWORD_LENGTH - len(password_chars)):
        password_chars.append(secrets.choice(all_chars))

    secrets.SystemRandom().shuffle(password_chars)
    password = "".join(password_chars)

    return _fix_consecutive_chars(password, all_chars)


def _fix_consecutive_chars(password: str, all_chars: str) -> str:
    result = list(password)
    for i in range(2, len(result)):
        if result[i] == result[i - 1] == result[i - 2]:
            for char in all_chars:
                if char != result[i]:
                    result[i] = char
                    break
    return "".join(result)


def _get_downloads_dir() -> Path:
    home = Path.home()
    downloads = home / "Downloads"
    return downloads if downloads.exists() else home


def _save_credentials_file(org_name: str, email: str, password: str) -> Path:
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

WARNING: Save this password securely - it will not be shown again.
WARNING: This file should be deleted after the password is stored securely.
"""

    filepath.write_text(content)
    try:
        os.chmod(filepath, 0o600)
    except OSError as e:
        logger.debug(f"Could not set file permissions (expected on Windows): {e}")

    return filepath


def _print_credentials_warning(filepath: Path) -> None:
    print(f"\n{'='*60}")
    print("NEW SUPPORT USER CREATED")
    print(f"Credentials saved to: {filepath}")
    print("Please store the password securely and delete the file.")
    print(f"{'='*60}\n")
