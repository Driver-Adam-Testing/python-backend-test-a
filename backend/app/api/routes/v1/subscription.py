from fastapi import APIRouter, HTTPException
from shared.billing.billing_service import BillingService
from shared.interfaces.billing.subscription_schema import (
    CreateSubscriptionRequest,
    SubscriptionRecord,
)

from app.api.auth import (
    M2MToken,
    SubscriptionManagerPermission,
    UserToken,
)
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_org_action

router = APIRouter()


@router.get(
    "",
    summary="Get orgs active subscription details",
)
def get_active_subscription(
    session: CurrentSession,
    user: UserToken,
) -> SubscriptionRecord:
    enforce_org_action(session, user, "subscription.read")
    subscription = BillingService(session).get_active_subscription_by_org(
        user.organization_id
    )
    if not subscription:
        raise HTTPException(404, "Subscription not found.")
    return subscription


@router.post(
    "", summary="Create a subscription", dependencies=[SubscriptionManagerPermission]
)
def create_subscription(
    session: CurrentSession, current_token: M2MToken, request: CreateSubscriptionRequest
) -> SubscriptionRecord:
    if current_token is None:
        raise HTTPException(403, "Forbidden")

    return BillingService(session).create_subscription(
        request.organization_id,
        request.plan_type,
        request.billing_frequency,
        request.start_date,
    )
