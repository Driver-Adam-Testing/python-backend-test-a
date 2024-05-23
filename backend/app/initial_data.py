import logging

from sqlmodel import Session

from driver_db.database.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init(session: Session) -> None:
    init_db(session)

    # user = session.exec(
    #     select(User).where(User.email == settings.FIRST_SUPERUSER)
    # ).first()
    # if not user:
    #     user_in = UserCreate(
    #         email=settings.FIRST_SUPERUSER,
    #         password=settings.FIRST_SUPERUSER_PASSWORD,
    #         is_superuser=True,
    #     )
    #     user = crud.create_user(session=session, user_create=user_in)


def main() -> None:
    logger.info("Creating initial data")
    with Session(engine) as session:
        init(session)
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
