from datetime import datetime

from fastapi import APIRouter, Query
from shared.interfaces.usage.usage_schema import (
    UsageBalance,
    UsageEventRecord,
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
    "/events",
    summary="Get Raw Usage Events",
)
def get_usage_events(
    session: CurrentSession, user: UserToken
) -> list[UsageEventRecord]:
    usage_service = UsageService(session)
    organization_id = user.organization_id
    return usage_service.get_usage_events(organization_id)


# # POST /api/v1/usage/webhook
# @router.post(
#     "/webhook",
#     summary="Webhook for usage events",
# )
# def usage_webhook(
#     session: CurrentSession, user: UserToken, credit_usage_event: CreditUsageEvent
# ) -> JSONResponse:
#     usage_service = UsageService(session)
#     organization_id = user.organization_id
#     user_id = user.user_id
#     event_type = UsageEventType.BASE_PLATFORM_USAGE_CREDIT
#     credit_amount = credit_usage_event.credit_amount
#
#     usage_service.issue_usage_credits(
#         organization_id, user_id, event_type, credit_amount
#     )
#     return JSONResponse(
#         status_code=status.HTTP_202_ACCEPTED, content={"message": "Accepted"}
#     )
