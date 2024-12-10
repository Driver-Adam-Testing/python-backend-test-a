from datetime import datetime
from enum import Enum
from uuid import UUID

from database.models_v1 import UsageEventType
from pydantic import BaseModel, Field, computed_field, model_validator
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
    balance: int = Field(default=0, description="Computed balance")
    unit: UsageMetricUnitType

    @model_validator(mode="before")
    def compute_balance(cls, values: dict) -> dict:
        _credits = values.get("credits", 0)
        _debits = values.get("debits", 0)
        print(f"credits: {_credits}, debits: {_debits}")
        values["balance"] = _credits + _debits if _credits > 0 else _debits
        return values

    def convert_to(self, target_unit: UsageMetricUnitType) -> "UsageBalance":
        """
        Convert credits, debits, and balance to the specified unit.
        """
        if self.unit == target_unit:
            return self

        conversion_fn = (
            sloc_to_bytes if target_unit == UsageMetricUnitType.BYTES else bytes_to_sloc
        )

        new_credits = conversion_fn(self.credits)
        new_debits = conversion_fn(self.debits)
        new_balance = conversion_fn(self.balance)

        return UsageBalance(
            credits=new_credits,
            debits=new_debits,
            balance=new_balance,
            unit=target_unit,
        )

    class Config:
        frozen = True


# AGENT_PIPELINE_USAGE_DEBIT = 1
# INSPECTOR_TECH_DOC_USAGE_DEBIT = 2
# INSPECTOR_CODE_DIFF_USAGE_DEBIT = 3
# ONBOARDING_USAGE_DEBIT = 4
# SUMMARIZATION_USAGE_DEBIT = 5
# BASE_PLATFORM_USAGE_CREDIT = 6
# ADDITIONAL_PLATFORM_USAGE_CREDIT = 7


class UsageEventSummary(BaseModel):
    """
    Usage Event Summary by usage type.
    """

    onboarding_usage: int
    tech_doc_usage: int
    code_diff_usage: int
    agent_pipeline_usage: int
    pdf_summarization_usage: int

    platform_usage_credits: int
    user_seat_count: int

    unit: UsageMetricUnitType

    def convert_to(self, target_unit: UsageMetricUnitType) -> "UsageEventSummary":
        """
        Convert usage values to the specified unit.
        """
        if self.unit == target_unit:
            return self

        conversion_fn = (
            sloc_to_bytes if target_unit == UsageMetricUnitType.BYTES else bytes_to_sloc
        )

        new_onboarding_usage = conversion_fn(self.onboarding_usage)
        new_tech_doc_usage = conversion_fn(self.tech_doc_usage)
        new_code_diff_usage = conversion_fn(self.code_diff_usage)
        new_agent_pipeline_usage = conversion_fn(self.agent_pipeline_usage)
        new_pdf_summarization_usage = conversion_fn(self.pdf_summarization_usage)
        new_platform_usage_credits = conversion_fn(self.platform_usage_credits)

        return UsageEventSummary(
            onboarding_usage=new_onboarding_usage,
            tech_doc_usage=new_tech_doc_usage,
            code_diff_usage=new_code_diff_usage,
            agent_pipeline_usage=new_agent_pipeline_usage,
            pdf_summarization_usage=new_pdf_summarization_usage,
            platform_usage_credits=new_platform_usage_credits,
            user_seat_count=self.user_seat_count,
            unit=target_unit,
        )

    class Config:
        frozen = True


class UsageEventRecord(BaseModel):
    id: UUID
    event_type: UsageEventType
    event_type_name: str
    session_id: UUID
    organization_id: str
    user_id: str
    event_source: str
    bytes_in: int
    bytes_out: int
    tokens_in: int
    tokens_out: int
    timestamp: datetime
    event_metadata: dict | None = None


class UsageCharge(BaseModel):
    asset_name: str

    timestamp: datetime
    bytes: int
    event_type: UsageEventType

    @computed_field
    @property
    def sloc(self) -> int:
        return abs(bytes_to_sloc(self.bytes))

    @computed_field
    @property
    def change_type(self) -> str:
        _change_type = ""

        if self.event_type == UsageEventType.ONBOARDING_USAGE_DEBIT:
            _change_type = "new"
        elif self.event_type == UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT:
            _change_type = "update"
        else:
            _change_type = "user_added"

        return _change_type
