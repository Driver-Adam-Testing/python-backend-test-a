from datetime import datetime

from database.models_v1 import UsageEvent, UsageEventType
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
    ) -> list[UsageEvent]:
        query = select(UsageEvent).where(
            UsageEvent.organization_id == organization_id,
            UsageEvent.event_type.in_(event_types),
        )
        if start_date:
            query = query.where(UsageEvent.timestamp >= start_date)
        if end_date:
            query = query.where(UsageEvent.timestamp <= end_date)
        return self.session.exec(query).all()
