from uuid import UUID

from fastapi import APIRouter, HTTPException
from shared.billing.billing_service import BillingService, SubscriptionServiceError
from shared.interfaces.billing.subscription_schema import (
    CreateSubscriptionRequest,
    SubscriptionRecord,
)

from app.api.auth import OrgManagerPermission, UserToken
from app.api.session import CurrentSession
from app.core.logger import logger

router = APIRouter()


@router.get(
    "", summary="Get orgs active subscription details", dependencies=[OrgManagerPermission]
)
def get_active_subscription(session: CurrentSession, user: UserToken) -> SubscriptionRecord:
    subscription = BillingService(session).get_active_subscription_by_org(user.organization_id)
    if not subscription:
        raise HTTPException(404, "Subscription not found.")
    return subscription


@router.post("", summary="Create a subscription", dependencies=[OrgManagerPermission])
def create_subscription(
    session: CurrentSession, user: UserToken, request: CreateSubscriptionRequest
) -> SubscriptionRecord:
    if user.organization_id != request.organization_id:
        raise HTTPException(403, "Bad request.")

    try:
        return BillingService(session).create_subscription(
            user.organization_id, request.plan_type, request.billing_frequency
        )
    except SubscriptionServiceError as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(400, str(e))


