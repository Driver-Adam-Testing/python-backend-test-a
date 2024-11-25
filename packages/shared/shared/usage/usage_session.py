from dataclasses import asdict
from uuid import UUID

from database.models_v1 import UsageSession, UsageSessionStatus
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from shared.interfaces.usage.event_metadata import UsageSessionMetadata


async def start_usage_session_async(
    organization_id: str, user_id: str, usage_context: dict[str, any]
) -> UUID:
    from database.db import async_engine

    async with AsyncSession(async_engine) as session:
        session_metadata = UsageSessionMetadata(**usage_context)
        session_metadata_dict = (
            session_metadata.dict()
            if hasattr(session_metadata, "dict")
            else asdict(session_metadata)
        )

        usage_session = UsageSession(
            status=UsageSessionStatus.RUNNING,
            organization_id=organization_id,
            user_id=user_id,
            session_metadata=session_metadata_dict,
        )
        session.add(usage_session)
        await session.commit()
        await session.refresh(usage_session)

        return usage_session.id


async def end_usage_session_async(session_id: UUID) -> None:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        result = await session.exec(
            select(UsageSession).where(UsageSession.id == session_id)
        )
        usage_session = result.first()
        if usage_session:
            usage_session.status = UsageSessionStatus.COMPLETED
            session.add(usage_session)
            await session.commit()


def start_usage_session_sync(
    organization_id: str, user_id: str, usage_context: dict[str, any]
) -> UUID:
    from database.db import engine

    with Session(engine) as session:
        # session_metadata = UsageSessionMetadata(**usage_context)
        # session_metadata_dict = (
        #     session_metadata.dict()
        #     if hasattr(session_metadata, "dict")
        #     else asdict(session_metadata)
        # )

        usage_session = UsageSession(
            status=UsageSessionStatus.RUNNING,
            organization_id=organization_id,
            user_id=user_id,
            session_metadata=usage_context,
        )
        session.add(usage_session)
        session.commit()
        session.refresh(usage_session)

        return usage_session.id


def end_usage_session_sync(session_id: UUID) -> None:
    from database.db import engine
    from sqlmodel import select

    with Session(engine) as session:
        result = session.exec(select(UsageSession).where(UsageSession.id == session_id))
        usage_session = result.first()
        if usage_session:
            usage_session.status = UsageSessionStatus.COMPLETED
            session.add(usage_session)
            session.commit()
