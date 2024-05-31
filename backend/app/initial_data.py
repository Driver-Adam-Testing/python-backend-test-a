import logging

from database.db import engine, init_db
from sqlmodel import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init(session: Session) -> None:
    init_db(session)
    pass


def main() -> None:
    logger.info("Creating initial data")
    with Session(engine) as session:
        init(session)
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
