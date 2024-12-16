import logging
import os

import botocore
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

# from database.db import create_engine
from database.models_v1 import UsageEvent
from sqlmodel import Session, create_engine
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

sm_client = botocore.session.get_session().create_client("secretsmanager")
cache_config = SecretCacheConfig()
cache = SecretCache(config=cache_config, client=sm_client)

database_url = (
    cache.get_secret_string(settings.DATABASE_URL_SECRET_NAME)
    if settings.ENVIRONMENT != "local"
    else settings.DATABASE_URL
)

engine = None


def get_engine() -> any:
    global engine
    if engine is None:
        engine = create_engine(database_url, pool_size=1)
    return engine


# # Python lambdas have to be synchronous ¯\_(ツ)_/¯
# # https://stackoverflow.com/questions/60455830/can-you-have-an-async-handler-in-lambda-python-3-6
def handler(event: dict, context: any) -> str:
    logger.info(event)
    logger.info(context)
    event_data = event["detail"]
    logger.info(event_data)
    with Session(get_engine()) as session:
        session_id = event_data["session_id"]
        usage_event = UsageEvent(
            session_id=session_id,
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
    return str(usage_event.id)
