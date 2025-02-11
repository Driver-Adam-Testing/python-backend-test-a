from datetime import datetime
from typing import Literal
from uuid import UUID

from database.models_v1 import UsageEvent, UsageEventType
from pydantic import BaseModel


class UsageSessionMetadata(BaseModel):
    content_type: Literal["codebase", "page", "pdf"]
    content_id: str
    events_sent: int = 0
    run_id: str | None = None
    content_name: str | None = None
    version_id: str | None = None


class UsagePaymentSessionMetadata(BaseModel):
    provider: str
    message: str
    event_kind: str


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
    event_type: UsageEventType
    event_metadata: UsageEventMetadata | None = None

    def into_usage_event(self) -> UsageEvent:
        usage_event = UsageEvent(
            event_type=self.event_type,
            session_id=self.session_id,
            organization_id=self.organization_id,
            user_id=self.user_id,
            event_source=self.event_source,
            bytes_in=self.bytes_in,
            bytes_out=self.bytes_out,
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            timestamp=self.timestamp,
            event_metadata=self.event_metadata.model_dump()
            if self.event_metadata
            else None,
        )
        return usage_event
