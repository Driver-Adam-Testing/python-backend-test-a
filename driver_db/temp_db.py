from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import psycopg2
import os
from alembic.config import Config
from alembic import command


# Define the database URL
TEST_DATABASE_URL = "postgresql+psycopg2://postgres:0Y43sfw7Hng1ZLHexDaxqCIbYmVQ5bhRKer5LlUjLmw@localhost/test_db"

# Create the engine
engine = create_engine(TEST_DATABASE_URL, echo=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create a new session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Drop the database if it exists
def drop_database():
    default_engine = create_engine(
        "postgresql+psycopg2://postgres:0Y43sfw7Hng1ZLHexDaxqCIbYmVQ5bhRKer5LlUjLmw@localhost/postgres")
    with default_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("DROP DATABASE IF EXISTS test_db"))


# Create the database if it doesn't exist
def create_database():
    default_engine = create_engine(
        "postgresql+psycopg2://postgres:0Y43sfw7Hng1ZLHexDaxqCIbYmVQ5bhRKer5LlUjLmw@localhost/postgres")
    with default_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("CREATE DATABASE test_db"))


# Apply Alembic migrations
def apply_migrations():
    alembic_cfg = Config("driver_db/database/alembic.ini")
    command.upgrade(alembic_cfg, "head")


# Create the database and tables
def init_db():
    SQLModel.metadata.create_all(bind=engine)


if __name__ == "__main__":
    try:
        drop_database()
        create_database()
        init_db()
        # apply_migrations()
    except psycopg2.OperationalError as e:
        if "does not exist" in str(e):
            create_database()
            init_db()
            # apply_migrations()
        else:
            raise