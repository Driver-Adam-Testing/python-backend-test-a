
import logging
import os

from database.db import create_engine
from database.models_v1 import UsageEvent
from sqlmodel import Session
from src.utils.config import settings

log_level = os.environ.get("LOG_LEVEL").upper() or logging.INFO
if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(log_level)
else:
    logging.basicConfig(level=log_level)

logger = logging.getLogger()
logger.info(f"Log level set to {log_level}")

engine = None


def get_engine() -> Session:
    global engine
    if engine is None:
        engine = create_engine(settings.DATABASE_URL)
    return engine


# # Python lambdas have to be synchronous ¯\_(ツ)_/¯
# # https://stackoverflow.com/questions/60455830/can-you-have-an-async-handler-in-lambda-python-3-6
def handler(event, context) -> str:
    logger.info(event)
    results = []
    event_data = event["detail"]
    logger.info(event_data)
    with Session(get_engine()) as session:
        usage_event = UsageEvent(
            session_id=event_data["session_id"],
            event_source=event_data["event_source"],
            event_type=event_data["event_type"],
            organization_id=event_data["organization_id"],
            user_id=event_data["user_id"],
            bytes_in=event_data["bytes_in"],
            bytes_out=event_data["bytes_out"],
            tokens_in=event_data["tokens_in"],
            tokens_out=event_data["tokens_out"],
            timestamp=event_data["timestamp"],
            event_metadata=event_data["event_metadata"],
        )
        session.add(usage_event)
        session.commit()
        session.refresh(usage_event)
        print(usage_event)
    return str(usage_event.id)
