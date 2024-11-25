from datetime import datetime
from typing import Literal
from uuid import UUID

from database.models_v1 import UsageEventType
from pydantic import BaseModel


class UsageSessionMetadata(BaseModel):
    content_type: Literal["codebase", "page", "pdf"]
    content_id: str
    events_sent: int = 0
    run_id: str | None = None


class UsageCreditSessionMetadata(BaseModel):
    provider: str
    message: str
    event_kind: str
    # {"stripe_webhook_event": "payment_succeeded"


class UsageEventMetadata(BaseModel):
    model: str
    provider: str
    input: dict
    output: str
    sloc: int = 0


class UsageMetric(BaseModel):
    session_id: UUID
    organization_id: str
    user_id: str
    event_source: str
    bytes_in: int
    bytes_out: int
    tokens_in: int
    tokens_out: int
    timestamp: datetime
    event_type: (
        UsageEventType  # Assuming UsageEventType is an Enum, you might use str or Enum
    )
    event_metadata: UsageEventMetadata
