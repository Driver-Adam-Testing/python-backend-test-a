from datetime import datetime
from typing import Literal

from database.models import UsageEvent, UsageEventType
from shared.repositories.base_repository import BaseRepository
from sqlmodel import Session, select


class UsageEventRepository(BaseRepository[UsageEvent]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, UsageEvent)

    def get_usage_events_by_types(
        self,
        organization_id: str,
        event_types: list[UsageEventType],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_direction: Literal["ASC", "DESC"] = "DESC",
    ) -> list[UsageEvent]:
        query = select(UsageEvent).where(
            UsageEvent.organization_id == organization_id,
            UsageEvent.event_type.in_(event_types),
        )

        if start_date:
            query = query.where(UsageEvent.timestamp >= start_date)
        if end_date:
            query = query.where(UsageEvent.timestamp <= end_date)

        if sort_direction == "DESC":
            query = query.order_by(UsageEvent.timestamp.desc())
        else:
            query = query.order_by(UsageEvent.timestamp.asc())

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        return self.session.exec(query).all()

    @staticmethod
    def billable_usage_event_types() -> list[UsageEventType]:
        return [
            UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT,
            UsageEventType.ONBOARDING_USAGE_DEBIT,
        ]

    @staticmethod
    def credit_usage_event_types() -> list[UsageEventType]:
        return [
            UsageEventType.BASE_PLATFORM_USAGE_CREDIT,
            UsageEventType.ADDITIONAL_PLATFORM_USAGE_CREDIT,
        ]
