from datetime import UTC, datetime

from app.core.logger import logger
from database.models_v1 import (
    BillingFrequency,
    PlanType,
    Subscription,
    SubscriptionStatus,
)
from sqlmodel import Session

from shared.interfaces.billing.subscription_schema import SubscriptionRecord
from shared.repositories.base_repository import BaseRepository


class SubscriptionServiceError(Exception):
    pass


class BillingService:
    def __init__(self: "BillingService", session: Session) -> None:
        self.session = session
        self.subscription_repository = BaseRepository(session, Subscription)

    def get_active_subscription_by_org(
        self: "BillingService", organization_id: str
    ) -> SubscriptionRecord | None:
        subscription = self.subscription_repository.get_by_conditions(
            [
                Subscription.organization_id == organization_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            ]
        )

        if not subscription:
            return None

        return SubscriptionRecord(**subscription.model_dump())

    def create_subscription(
        self: "BillingService",
        organization_id: str,
        plan_type: PlanType,
        billing_frequency: BillingFrequency,
        start_date: datetime | None = None,
    ) -> SubscriptionRecord:
        subscription = self.get_active_subscription_by_org(organization_id)
        if subscription:
            logger.info(
                f"Organization {organization_id} already has an active subscription"
            )
            raise SubscriptionServiceError(
                "Organization already has an active subscription"
            )

        subscription = Subscription(
            organization_id=organization_id,
            plan_type=plan_type,
            billing_frequency=billing_frequency,
            created_at=start_date if start_date else datetime.now(tz=UTC),
        )
        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)
        return SubscriptionRecord(**subscription.model_dump())
