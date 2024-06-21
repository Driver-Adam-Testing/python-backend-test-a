from collections.abc import Generator
from typing import Annotated

from database.db import engine
from fastapi import Depends
from sqlmodel import Session


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


CurrentSession = Annotated[Session, Depends(get_db)]
