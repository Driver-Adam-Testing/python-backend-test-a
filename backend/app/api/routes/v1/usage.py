from datetime import datetime

from fastapi import APIRouter, Query
from shared.interfaces.usage.usage_schema import (
    UsageBalance,
    UsageCharge,
    UsageEventSummary,
)
from shared.usage.usage_service import UsageService

from app.api.auth import UserToken
from app.api.routes.v2.query_utils import Pagination
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_super_admin

router = APIRouter()


@router.get(
    "/balance",
    summary="Get Usage Balance Summary",
)
def get_usage_balance(session: CurrentSession, user: UserToken) -> UsageBalance:
    enforce_super_admin(session, user)
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
    enforce_super_admin(session, user)
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
    session: CurrentSession, user: UserToken, pagination: Pagination
) -> list[UsageCharge]:
    enforce_super_admin(session, user)
    limit = pagination.limit
    offset = pagination.offset
    sort_direction = pagination.sort_direction

    return UsageService(session).get_charges(
        user.organization_id, limit=limit, offset=offset, sort_direction=sort_direction
    )


# TODO - fix M2M token validation. This should not be callable by customers. It is currently broken.
# I think this may start working again when we remove the old auth system. Places where the current impl
# prevents this from working:
#
# 1. main.py requries user auth (require_jwt) for all endpoints underneath /studio/v1
# 2. auth.py require_permission requires a user jwt (require_jwt) to check permissions. M2M tokens have permissions, but not a user. They're a machine, not a User.
#
# The require_m2m_jwt in this endpoint never gets reached because of (at least) those reasons as things stand.
#
# jwt_middleware
# @router.post(
#     "/credit",
#     summary="Issue Usage Credits",
#     dependencies=[UsageCreditPermission],
# )
# def credit_usage(
#     session: CurrentSession,
#     current_token: M2MToken,
#     credit_usage_event: CreditUsageEvent,
# ) -> JSONResponse:

#     if current_token is None:
#         raise HTTPException(403, "Forbidden")

#     aws_client = boto3.client(
#         "events",
#         region_name=settings.AWS_REGION,
#         aws_access_key_id=settings.S3ADMIN_AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=settings.S3ADMIN_AWS_SECRET_ACCESS_KEY,
#     )

#     organization_id = credit_usage_event.organization_id
#     user_id = (
#         "SYSTEM" if credit_usage_event.user_id is None else credit_usage_event.user_id
#     )
#     event_type = UsageEventType.BASE_PLATFORM_USAGE_CREDIT
#     credit_amount = sloc_to_bytes(credit_usage_event.sloc_credit_amount)

#     UsageService(session, aws_client).issue_usage_credits(
#         organization_id, user_id, event_type, credit_amount
#     )
#     return JSONResponse(
#         status_code=status.HTTP_202_ACCEPTED, content={"message": "Accepted"}
#     )
