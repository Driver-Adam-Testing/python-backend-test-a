from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Auth0EventData(BaseModel):
    """Auth0 event data from EventBridge detail.data"""

    type: str = Field(
        description="Event type (s, ss, sdu, organization_member_*, sapi, etc.)"
    )
    user_id: str | None = Field(default=None, description="Auth0 user ID")
    organization_id: str | None = Field(
        default=None, description="Auth0 organization ID"
    )
    log_id: str | None = Field(default=None, description="Alternative log ID location")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional event details"
    )


class Auth0EventDetail(BaseModel):
    """Auth0 EventBridge event detail"""

    log_id: str | None = Field(
        default=None, description="Unique log ID for idempotency"
    )
    data: Auth0EventData = Field(description="Event data payload")

class Auth0EventBridgeEvent(BaseModel):
    """Complete Auth0 EventBridge event structure"""

    id: str | None = Field(default=None, description="EventBridge event ID")
    source: str | None = Field(default=None, description="Event source")
    detail_type: str | None = Field(
        default=None, alias="detail-type", description="Event detail type"
    )
    detail: Auth0EventDetail = Field(description="Event details")
    time: datetime | None = Field(default=None, description="Event timestamp")


class Auth0EventProcessingResult(BaseModel):
    """Result of processing an Auth0 event"""

    log_id: str | None
    event_type: str
    processed: bool
    error: str | None = Field(default=None)
    entities_updated: list[str] = Field(
        default_factory=list,
        description="List of entity types updated (user, org, membership)",
    )


def extract_log_id(event: Auth0EventBridgeEvent) -> str:
    """
    Extract log_id from Auth0 event for idempotency.
    Tries multiple locations based on the example code patterns.
    """
    # Try detail.log_id first (primary location)
    if event.detail.log_id:
        return event.detail.log_id

    # Try detail.data.log_id (alternative location)
    if event.detail.data.log_id:
        return event.detail.data.log_id

    # Fall back to event.id if available
    if event.id:
        return event.id

    # Last resort - this shouldn't happen with proper Auth0 events
    raise ValueError("No log_id found in Auth0 event - cannot ensure idempotency")


