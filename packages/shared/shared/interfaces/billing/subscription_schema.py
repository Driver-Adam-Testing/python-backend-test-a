from datetime import date, datetime
from uuid import UUID

from database.models import BillingFrequency, PlanType, SubscriptionStatus
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, computed_field


class SubscriptionRecord(BaseModel):
    id: UUID
    organization_id: str
    plan_type: PlanType
    status: SubscriptionStatus
    billing_frequency: BillingFrequency
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def start_date(self) -> date:
        return self.created_at.date()

    @computed_field
    @property
    def end_date(self) -> date:
        start_date = self.start_date
        end_date = (
            start_date + relativedelta(months=1)
            if self.billing_frequency == BillingFrequency.MONTHLY
            else start_date + relativedelta(years=1)
        )
        return end_date


class CreateSubscriptionRequest(BaseModel):
    plan_type: PlanType
    billing_frequency: BillingFrequency
    organization_id: str
    start_date: datetime | None = None
