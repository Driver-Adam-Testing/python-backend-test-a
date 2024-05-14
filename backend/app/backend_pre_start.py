import logging

from database import engine
from sqlalchemy import Engine, text
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    try:
        with Session(db_engine) as session:
            # Try to create session to check if DB is awake
            session.exec(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def config_extensions(db_engine: Engine) -> None:
    try:
        with db_engine.connect() as connection:
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    except Exception as e:
        logger.exception(e)
        raise e


def main() -> None:
    logger.info("Initializing service")
    init(engine)
    # logger.info("Configuring db extensions")
    # config_extensions(engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
