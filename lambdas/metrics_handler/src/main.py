""" """

import logging
import os

import botocore
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from database.db import create_engine
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

    sm_client = botocore.session.get_session().create_client("secretsmanager")
    cache_config = SecretCacheConfig()
    cache = SecretCache(config=cache_config, client=sm_client)

    database_url = (
        cache.get_secret_string(settings.DATABASE_URL_SECRET_NAME)
        if settings.ENVIRONMENT != "local"
        else settings.DATABASE_URL
    )

    results = []

    with Session(engine) as session:
        for record in event["Records"]:
            logger.info(record)

    return "Ok"
