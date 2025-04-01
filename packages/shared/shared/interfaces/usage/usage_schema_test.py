# from datetime import datetime

# import pytest
# from dateutil import parser
# from pydantic import ValidationError
# from shared.interfaces.usage.usage_schema import (
#     UsageBalance,
#     UsageEventRange,
#     UsageEventSummary,
#     UsageMetricUnitType,
# )
# from shared.usage.utils import bytes_to_sloc, sloc_to_bytes


# @pytest.fixture
# def usage_balance_sloc() -> UsageBalance:
#     return UsageBalance(credits=100, debits=50, unit=UsageMetricUnitType.SLOC)


# @pytest.fixture
# def usage_balance_bytes() -> UsageBalance:
#     return UsageBalance(
#         credits=sloc_to_bytes(100),  # 5000
#         debits=sloc_to_bytes(50),  # 2500
#         unit=UsageMetricUnitType.BYTES,
#     )


# @pytest.fixture
# def usage_balance_zero_credits() -> UsageBalance:
#     return UsageBalance(credits=0, debits=50, unit=UsageMetricUnitType.SLOC)


# @pytest.fixture
# def usage_balance_zero_debits() -> UsageBalance:
#     return UsageBalance(credits=100, debits=0, unit=UsageMetricUnitType.SLOC)


# @pytest.fixture
# def usage_event_summary_sloc() -> UsageEventSummary:
#     return UsageEventSummary(
#         onboarding_usage=100,
#         tech_doc_usage=200,
#         code_diff_usage=300,
#         agent_pipeline_usage=400,
#         pdf_summarization_usage=500,
#         platform_usage_credits=600,
#         user_seat_count=10,
#         unit=UsageMetricUnitType.SLOC,
#     )


# @pytest.fixture
# def usage_event_summary_bytes() -> UsageEventSummary:
#     return UsageEventSummary(
#         onboarding_usage=sloc_to_bytes(100),
#         tech_doc_usage=sloc_to_bytes(200),
#         code_diff_usage=sloc_to_bytes(300),
#         agent_pipeline_usage=sloc_to_bytes(400),
#         pdf_summarization_usage=sloc_to_bytes(500),
#         platform_usage_credits=sloc_to_bytes(600),
#         user_seat_count=10,
#         unit=UsageMetricUnitType.BYTES,
#     )


# def test_sloc_to_bytes() -> None:
#     assert sloc_to_bytes(100) == 5000


# def test_bytes_to_sloc() -> None:
#     assert bytes_to_sloc(5000) == 100


# def test_compute_balance(usage_balance_sloc: UsageBalance) -> None:
#     assert usage_balance_sloc.balance == 150


# def test_compute_balance_zero_credits(usage_balance_zero_credits: UsageBalance) -> None:
#     assert usage_balance_zero_credits.balance == 50


# def test_compute_balance_zero_debits(usage_balance_zero_debits: UsageBalance) -> None:
#     assert usage_balance_zero_debits.balance == 100


# def test_covert_sloc_to_sloc(usage_balance_sloc: UsageBalance) -> None:
#     new_balance = usage_balance_sloc.convert_to(UsageMetricUnitType.SLOC)
#     assert new_balance == usage_balance_sloc


# def test_covert_bytes_to_bytes(usage_balance_bytes: UsageBalance) -> None:
#     new_balance = usage_balance_bytes.convert_to(UsageMetricUnitType.BYTES)
#     assert new_balance == usage_balance_bytes


# def test_convert_to_bytes(usage_balance_sloc: UsageBalance) -> None:
#     new_balance = usage_balance_sloc.convert_to(UsageMetricUnitType.BYTES)
#     # test the values are unchanged
#     assert usage_balance_sloc.unit == UsageMetricUnitType.SLOC
#     assert usage_balance_sloc.credits == 100
#     assert usage_balance_sloc.debits == 50
#     # test the new values
#     assert new_balance.unit == UsageMetricUnitType.BYTES
#     assert new_balance.credits == sloc_to_bytes(100)
#     assert new_balance.debits == sloc_to_bytes(50)


# def test_convert_to_sloc(usage_balance_bytes: UsageBalance) -> None:
#     new_balance = usage_balance_bytes.convert_to(UsageMetricUnitType.SLOC)
#     # test the values are unchanged
#     assert usage_balance_bytes.unit == UsageMetricUnitType.BYTES
#     assert usage_balance_bytes.credits == sloc_to_bytes(100)
#     assert usage_balance_bytes.debits == sloc_to_bytes(50)
#     # test the new values
#     assert new_balance.unit == UsageMetricUnitType.SLOC
#     assert new_balance.credits == 100
#     assert new_balance.debits == 50


# def test_convert_to_bytes_with_zero_credits(
#     usage_balance_zero_credits: UsageBalance,
# ) -> None:
#     converted_balance = usage_balance_zero_credits.convert_to(UsageMetricUnitType.BYTES)
#     assert converted_balance.unit == UsageMetricUnitType.BYTES
#     assert converted_balance.credits == 0
#     assert converted_balance.debits == sloc_to_bytes(50)
#     assert converted_balance.balance == sloc_to_bytes(50)


# def test_convert_to_sloc_with_zero_debits(
#     usage_balance_zero_debits: UsageBalance,
# ) -> None:
#     converted_balance = usage_balance_zero_debits.convert_to(UsageMetricUnitType.SLOC)
#     assert converted_balance.unit == UsageMetricUnitType.SLOC
#     assert converted_balance.credits == 100
#     assert converted_balance.debits == 0
#     assert converted_balance.balance == 100


# def test_convert_to_bytes_and_back(usage_balance_sloc: UsageBalance) -> None:
#     converted_to_bytes = usage_balance_sloc.convert_to(UsageMetricUnitType.BYTES)
#     assert converted_to_bytes.unit == UsageMetricUnitType.BYTES
#     converted_back_to_sloc = converted_to_bytes.convert_to(UsageMetricUnitType.SLOC)
#     assert converted_back_to_sloc.unit == UsageMetricUnitType.SLOC
#     assert converted_back_to_sloc.credits == 100
#     assert converted_back_to_sloc.debits == 50
#     assert converted_back_to_sloc.balance == 150


# def test_event_summary_convert_to_bytes(
#     usage_event_summary_sloc: UsageEventSummary,
# ) -> None:
#     converted = usage_event_summary_sloc.convert_to(UsageMetricUnitType.BYTES)
#     # test original values are unchanged
#     assert usage_event_summary_sloc.unit == UsageMetricUnitType.SLOC
#     assert usage_event_summary_sloc.onboarding_usage == 100
#     assert usage_event_summary_sloc.tech_doc_usage == 200
#     assert usage_event_summary_sloc.code_diff_usage == 300
#     # test new values
#     assert converted.unit == UsageMetricUnitType.BYTES
#     assert converted.onboarding_usage == sloc_to_bytes(100)
#     assert converted.tech_doc_usage == sloc_to_bytes(200)
#     assert converted.code_diff_usage == sloc_to_bytes(300)


# def test_event_summary_convert_to_sloc(
#     usage_event_summary_bytes: UsageEventSummary,
# ) -> None:
#     converted = usage_event_summary_bytes.convert_to(UsageMetricUnitType.SLOC)
#     # test original values are unchanged
#     assert usage_event_summary_bytes.unit == UsageMetricUnitType.BYTES
#     assert usage_event_summary_bytes.onboarding_usage == sloc_to_bytes(100)
#     assert usage_event_summary_bytes.tech_doc_usage == sloc_to_bytes(200)
#     assert usage_event_summary_bytes.code_diff_usage == sloc_to_bytes(300)
#     # test new values
#     assert converted.unit == UsageMetricUnitType.SLOC
#     assert converted.onboarding_usage == 100
#     assert converted.tech_doc_usage == 200
#     assert converted.code_diff_usage == 300


# def test_usage_event_range() -> None:
#     st = parser.parse("2024-12-02T00:00:00Z")
#     et = parser.parse("2024-12-31T23:59:59Z")
#     event_range = UsageEventRange(start_date=st, end_date=et)
#     assert event_range.start_date.tzinfo is not None
#     assert event_range.end_date.tzinfo is not None
#     with pytest.raises(ValidationError):
#         UsageEventRange(start_date=datetime(2021, 1, 1), end_date=datetime(2020, 1, 31))
