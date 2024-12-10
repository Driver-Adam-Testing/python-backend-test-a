from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.auth import OrgManagerPermission, UserToken
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.subscription_schema import (
    CreateSubscriptionRequest,
    PlanRecord,
    SubscriptionRecord,
)
from app.services.billing_service import BillingService

router = APIRouter()


@router.get(
    "", summary="Get org subscription details", dependencies=[OrgManagerPermission]
)
def get_subscription(session: CurrentSession, user: UserToken) -> SubscriptionRecord:
    subscription = BillingService(session).get_subscription_by_org(user.organization_id)
    if not subscription:
        raise HTTPException(404, "Subscription not found.")
    return subscription


@router.post("", summary="Create a subscription", dependencies=[OrgManagerPermission])
def create_subscription(
    session: CurrentSession, user: UserToken, request: CreateSubscriptionRequest
) -> UUID:
    if user.organization_id != request.organization_id:
        raise HTTPException(400, "Bad request.")

    return BillingService(session).create_subscription(
        user.organization_id, request.plan_id
    )


@router.get("/plans", summary="Get all plans", dependencies=[OrgManagerPermission])
def get_plans(session: CurrentSession) -> list[PlanRecord]:
    logger.info("Getting all plans")
    billing_service = BillingService(session)
    return billing_service.get_plans()
