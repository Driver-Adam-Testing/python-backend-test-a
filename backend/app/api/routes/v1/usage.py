from datetime import datetime

import boto3
from database.models_v1 import UsageEventType
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from shared.interfaces.usage.usage_schema import (
    CreditUsageEvent,
    UsageBalance,
    UsageCharge,
    UsageEventRange,
    UsageEventSummary,
)
from shared.usage.usage_service import UsageService
from shared.usage.utils import sloc_to_bytes

from app.api.auth import M2MToken, UsageCreditPermission, UserToken
from app.api.session import CurrentSession
from app.core.config import settings

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


@router.post(
    "/credit",
    summary="Issue Usage Credits",
    dependencies=[UsageCreditPermission],
)
def credit_usage(
    session: CurrentSession,
    current_token: M2MToken,
    credit_usage_event: CreditUsageEvent,
) -> JSONResponse:
    if current_token is None:
        raise HTTPException(403, "Forbidden")

    aws_client = boto3.client(
        "events",
        region_name="us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    organization_id = credit_usage_event.organization_id
    user_id = (
        "SYSTEM" if credit_usage_event.user_id is None else credit_usage_event.user_id
    )
    event_type = UsageEventType.BASE_PLATFORM_USAGE_CREDIT
    credit_amount = sloc_to_bytes(credit_usage_event.sloc_credit_amount)

    UsageService(session, aws_client).issue_usage_credits(
        organization_id, user_id, event_type, credit_amount
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"message": "Accepted"}
    )
