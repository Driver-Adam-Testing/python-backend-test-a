from enum import Enum

from pydantic import BaseModel, model_validator
from shared.usage.utils import bytes_to_sloc, sloc_to_bytes


class UsageMetricUnitType(str, Enum):
    BYTES = "bytes"
    SLOC = "sloc"


class CreditUsageEvent(BaseModel):
    credit_amount: int
    unit: UsageMetricUnitType


class UsageBalance(BaseModel):
    credits: int
    debits: int
    balance: int = 0  # Initialize with a default value, though it's computed
    unit: UsageMetricUnitType

    @model_validator(mode="before")
    def compute_balance(cls, values: dict) -> dict:
        _credits = values.get("credits", 0)
        _debits = values.get("debits", 0)
        print(f"credits: {_credits}, debits: {_debits}")
        values["balance"] = _credits + _debits if _credits > 0 else _debits
        return values

    def convert_to(self, target_unit: UsageMetricUnitType) -> None:
        """
        Convert credits, debits, and balance to the specified unit.
        """
        if self.unit == target_unit:
            return

        if target_unit == UsageMetricUnitType.BYTES:
            self.credits = sloc_to_bytes(self.credits)
            self.debits = sloc_to_bytes(self.debits)
            self.balance = sloc_to_bytes(self.balance)
        elif target_unit == UsageMetricUnitType.SLOC:
            self.credits = bytes_to_sloc(self.credits)
            self.debits = bytes_to_sloc(self.debits)
            self.balance = bytes_to_sloc(self.balance)

        self.unit = target_unit


# AGENT_PIPELINE_USAGE_DEBIT = 1
# INSPECTOR_TECH_DOC_USAGE_DEBIT = 2
# INSPECTOR_CODE_DIFF_USAGE_DEBIT = 3
# ONBOARDING_USAGE_DEBIT = 4
# SUMMARIZATION_USAGE_DEBIT = 5
# BASE_PLATFORM_USAGE_CREDIT = 6
# ADDITIONAL_PLATFORM_USAGE_CREDIT = 7


class UsageEventSummary(BaseModel):
    """
    Usage Event Details
    """

    onboarding_usage: int
    tech_doc_usage: int
    code_diff_usage: int
    agent_pipeline_usage: int
    pdf_summarization_usage: int

    platform_usage_credits: int
    user_seat_count: int

    unit: UsageMetricUnitType

    def convert_to(self, target_unit: UsageMetricUnitType) -> None:
        """
        Convert credits, debits, and balance to the specified unit.
        """
        if self.unit == target_unit:
            return

        if target_unit == UsageMetricUnitType.BYTES:
            self.onboarding_usage = sloc_to_bytes(self.onboarding_usage)
            self.tech_doc_usage = sloc_to_bytes(self.tech_doc_usage)
            self.code_diff_usage = sloc_to_bytes(self.code_diff_usage)
            self.agent_pipeline_usage = sloc_to_bytes(self.agent_pipeline_usage)
            self.pdf_summarization_usage = sloc_to_bytes(self.pdf_summarization_usage)
            self.platform_usage_credits = sloc_to_bytes(self.platform_usage_credits)
        elif target_unit == UsageMetricUnitType.SLOC:
            self.onboarding_usage = bytes_to_sloc(self.onboarding_usage)
            self.tech_doc_usage = bytes_to_sloc(self.tech_doc_usage)
            self.code_diff_usage = bytes_to_sloc(self.code_diff_usage)
            self.agent_pipeline_usage = bytes_to_sloc(self.agent_pipeline_usage)
            self.pdf_summarization_usage = bytes_to_sloc(self.pdf_summarization_usage)
            self.platform_usage_credits = bytes_to_sloc(self.platform_usage_credits)

        self.unit = target_unit
