from datetime import datetime

from fastapi import APIRouter, Query
from shared.interfaces.usage.usage_schema import (
    UsageBalance,
    UsageCharge,
    UsageEventRange,
    UsageEventSummary,
)
from shared.usage.usage_service import UsageService

from app.api.auth import UserToken
from app.api.session import CurrentSession

router = APIRouter()


@router.get(
    "/balance",
    summary="Get Usage Balance Summary",
)
def get_usage_balance(session: CurrentSession, user: UserToken) -> UsageBalance:
    usage_service = UsageService(session)
    organization_id = user.organization_id
    usage_balance = usage_service.get_usage_balance(organization_id)
    return usage_balance


@router.get(
    "/summary",
    summary="Get Detailed Usage Summary",
)
def get_usage_summary(
    session: CurrentSession,
    user: UserToken,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
) -> UsageEventSummary:
    usage_service = UsageService(session)
    organization_id = user.organization_id
    usage_summary = usage_service.get_usage_summary(
        organization_id, start_date, end_date
    )
    return usage_summary


@router.get(
    "/charges",
    summary="Get Recent Usage Charges",
)
def get_charges(
    session: CurrentSession,
    user: UserToken,
    start_date: datetime | None = Query(
        None,
        description="Start date for the range of charges. ISO 8601 format required",
    ),
    end_date: datetime | None = Query(
        None, description="End date for the range of charges. ISO 8601 format required"
    ),
) -> list[UsageCharge]:
    return UsageService(session).get_charges(
        user.organization_id, UsageEventRange(start_date=start_date, end_date=end_date)
    )
