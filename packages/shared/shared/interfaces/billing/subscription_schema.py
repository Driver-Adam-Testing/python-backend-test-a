from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from database.models_v1 import (
    PlanType,
    SubscriptionStatus,
    BillingFrequency
)


class SubscriptionRecord(BaseModel):
    id: UUID
    organization_id: str
    plan_type: PlanType
    status: SubscriptionStatus
    billing_frequency: BillingFrequency
    created_at: datetime
    updated_at: datetime


class CreateSubscriptionRequest(BaseModel):
    plan_type: PlanType
    billing_frequency: BillingFrequency
    organization_id: str
