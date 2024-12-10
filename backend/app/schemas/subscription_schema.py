from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class PlanRecord(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    billing_frequency: str
    base_usage_price: float
    base_seat_price: float
    created_at: datetime
    updated_at: datetime

    # class Config:
    #     orm_mode = True


class SubscriptionRecord(BaseModel):
    id: UUID
    organization_id: str
    plan_id: UUID
    status: str
    billing_frequency: str
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: datetime
    plan: PlanRecord

    # class Config:
    #     orm_mode = True


class CreateSubscriptionRequest(BaseModel):
    plan_id: UUID
    organization_id: str
