import pytest
from shared.usage.utils import sloc_to_bytes

from packages.shared.shared.interfaces.usage.usage_schema import (
    UsageBalance,
    UsageEventSummary,
    UsageMetricUnitType,
)


@pytest.fixture
def usage_balance_sloc() -> UsageBalance:
    return UsageBalance(credits=100, debits=50, unit=UsageMetricUnitType.SLOC)


@pytest.fixture
def usage_balance_bytes() -> UsageBalance:
    return UsageBalance(
        credits=sloc_to_bytes(100),
        debits=sloc_to_bytes(50),
        unit=UsageMetricUnitType.BYTES,
    )


@pytest.fixture
def usage_event_summary_sloc() -> UsageEventSummary:
    return UsageEventSummary(
        onboarding_usage=100,
        tech_doc_usage=200,
        code_diff_usage=300,
        agent_pipeline_usage=400,
        pdf_summarization_usage=500,
        platform_usage_credits=600,
        user_seat_count=10,
        unit=UsageMetricUnitType.SLOC,
    )


@pytest.fixture
def usage_event_summary_bytes() -> UsageEventSummary:
    return UsageEventSummary(
        onboarding_usage=sloc_to_bytes(100),
        tech_doc_usage=sloc_to_bytes(200),
        code_diff_usage=sloc_to_bytes(300),
        agent_pipeline_usage=sloc_to_bytes(400),
        pdf_summarization_usage=sloc_to_bytes(500),
        platform_usage_credits=sloc_to_bytes(600),
        user_seat_count=10,
        unit=UsageMetricUnitType.BYTES,
    )


def test_compute_balance(usage_balance_sloc: UsageBalance) -> None:
    assert usage_balance_sloc.balance == 150


def test_convert_to_bytes(usage_balance_sloc: UsageBalance) -> None:
    usage_balance_sloc.convert_to(UsageMetricUnitType.BYTES)
    assert usage_balance_sloc.unit == UsageMetricUnitType.BYTES
    assert usage_balance_sloc.credits == sloc_to_bytes(100)
    assert usage_balance_sloc.debits == sloc_to_bytes(50)


def test_convert_to_sloc(usage_balance_bytes: UsageBalance) -> None:
    usage_balance_bytes.convert_to(UsageMetricUnitType.SLOC)
    assert usage_balance_bytes.unit == UsageMetricUnitType.SLOC
    assert usage_balance_bytes.credits == 100
    assert usage_balance_bytes.debits == 50


def test_event_summary_convert_to_bytes(
    usage_event_summary_sloc: UsageEventSummary,
) -> None:
    usage_event_summary_sloc.convert_to(UsageMetricUnitType.BYTES)
    assert usage_event_summary_sloc.unit == UsageMetricUnitType.BYTES
    assert usage_event_summary_sloc.onboarding_usage == sloc_to_bytes(100)
    assert usage_event_summary_sloc.tech_doc_usage == sloc_to_bytes(200)
    assert usage_event_summary_sloc.code_diff_usage == sloc_to_bytes(300)


def test_event_summary_convert_to_sloc(
    usage_event_summary_bytes: UsageEventSummary,
) -> None:
    usage_event_summary_bytes.convert_to(UsageMetricUnitType.SLOC)
    assert usage_event_summary_bytes.unit == UsageMetricUnitType.SLOC
    assert usage_event_summary_bytes.onboarding_usage == 100
    assert usage_event_summary_bytes.tech_doc_usage == 200
    assert usage_event_summary_bytes.code_diff_usage == 300
