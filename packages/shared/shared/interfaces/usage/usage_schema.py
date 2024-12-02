from enum import Enum

from pydantic import BaseModel, model_validator


class UsageMetricUnitType(str, Enum):
    BYTES = "bytes"
    SLOC = "SLOC"


class CreditUsageEvent(BaseModel):
    credit_amount: int
    unit: UsageMetricUnitType


class UsageBalance(BaseModel):
    credits: int
    debits: int
    balance: int = 0  # Initialize with a default value, though it's computed
    unit: UsageMetricUnitType

    @model_validator(mode="before")
    def compute_balance(cls, values):
        _credits = values.get("credits", 0)
        _debits = values.get("debits", 0)
        print(f"credits: {_credits}, debits: {_debits}")
        values["balance"] = _credits + _debits if _credits > 0 else _debits
        return values


class UsageEventSummary(BaseModel):
    """
    Usage Event Details
    """

    onboarding_usage: int
    inspector_usage: int
    agent_pipeline_usage: int
    pdf_summarization_usage: int

    onboarding_session_count: int
    inspector_session_count: int
    agent_pipeline_session_count: int
    pdf_summarization_session_count: int

    unit: UsageMetricUnitType
