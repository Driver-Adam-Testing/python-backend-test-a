import re
from dataclasses import dataclass

from database.models import BillingFrequency, PlanType

SUPPORT_EMAIL = "support@driverai.com"
SUPPORT_NAME = "Driver Support"
DEFAULT_SLOC_CREDITS = 500_000
SYSTEM_USER_ID = "SYSTEM"

ORG_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


@dataclass(frozen=True)
class OrgSetupConfig:
    """Configuration for creating a new organization."""

    org_name: str
    display_name: str
    admin_emails: list[str]
    plan_type: PlanType
    billing_frequency: BillingFrequency
    sloc_credits: int = DEFAULT_SLOC_CREDITS

    def __post_init__(self) -> None:
        if not ORG_NAME_PATTERN.match(self.org_name):
            raise ValueError(
                f"Invalid organization name '{self.org_name}'. "
                "Must start with lowercase letter/digit and contain only "
                "lowercase letters, digits, hyphens, underscores."
            )

    @property
    def admin_emails_with_support(self) -> list[str]:
        return list(dict.fromkeys([SUPPORT_EMAIL, *self.admin_emails]))

    @property
    def non_support_admin_emails(self) -> list[str]:
        return [e for e in self.admin_emails if e != SUPPORT_EMAIL]


@dataclass(frozen=True)
class CreditsConfig:
    """Configuration for issuing credits to an existing organization."""

    organization_id: str
    sloc_amount: int
    user_id: str = SUPPORT_EMAIL
