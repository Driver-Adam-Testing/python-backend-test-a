from datetime import date
from uuid import UUID

from app.core.logger import logger
from database.models_v1 import Plan, Subscription
from dateutil.relativedelta import relativedelta
from sqlmodel import Session

from shared.interfaces.billing.subscription_schema import PlanRecord, SubscriptionRecord
from shared.repositories.base_repository import BaseRepository


class BillingService:
    def __init__(self: "BillingService", session: Session) -> None:
        self.session = session
        self.plan_repository = BaseRepository(session, Plan)
        self.subscription_repository = BaseRepository(session, Subscription)

    def get_plans(self: "BillingService") -> [PlanRecord]:
        plans = self.plan_repository.get_all()
        return [PlanRecord(**plan.model_dump()) for plan in plans]

    def get_subscription_by_org(
        self: "BillingService", organization_id: str
    ) -> SubscriptionRecord | None:
        subscription = self.subscription_repository.get_by_conditions(
            [Subscription.organization_id == organization_id]
        )

        if not subscription:
            return None

        return SubscriptionRecord(
            id=subscription.id,
            organization_id=subscription.organization_id,
            plan_id=subscription.plan_id,
            status=subscription.status.value,
            billing_frequency=subscription.billing_frequency,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            plan=PlanRecord(**subscription.plan.model_dump()),
        )

    def create_subscription(
        self: "BillingService", organization_id: str, plan_id: UUID
    ) -> UUID:
        subscription = self.subscription_repository.get_by_conditions(
            [Subscription.organization_id == organization_id]
        )
        if subscription:
            logger.info(
                f"Subscription already exists for organization {organization_id}"
            )
            return subscription.id

        plan = self.plan_repository.get(plan_id)
        # calculate billing period start and end
        start_date = date.today()
        if plan.billing_frequency == "monthly":
            end_date = start_date + relativedelta(months=1)
        else:
            end_date = start_date + relativedelta(years=1)
        # end_date = (start_date.replace(month=start_date.month+1) if plan.billing_frequency == "monthly" else start_date.replace(year=start_date.year+1))
        print(f" billing period start_date: {start_date}, end_date: {end_date}")

        subscription = Subscription(
            organization_id=organization_id,
            plan_id=plan_id,
            billing_frequency=plan.billing_frequency,
            start_date=start_date,
            end_date=end_date,
        )
        self.session.add(subscription)
        self.session.commit()
        return subscription.id
