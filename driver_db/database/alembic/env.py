import datetime
from logging.config import fileConfig

from alembic import context
from database.config import settings
from database.models_v1 import SQLModel as V1
from database.models_v2 import SQLModel as V2
from sqlalchemy import engine_from_config, inspect, pool, text
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel  # Import SQLModel

config = context.config
fileConfig(str(config.config_file_name))

print(V1)
print(V2)

target_metadata = SQLModel.metadata


def get_url() -> str:
    return str(settings.SQLALCHEMY_DATABASE_URI)


def include_object(
    object: any, name: str, type_: str, reflected: any, compare_to: any
) -> bool:
    return not (type_ == "table" and name == "v2_full_node")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def table_exists(connection: Connection, table_name: str) -> bool:
    inspector = inspect(connection)
    return table_name in inspector.get_table_names()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            # Check if alembic_version table exists
            if table_exists(connection, "alembic_version"):
                # Lock the alembic_version table to prevent concurrency issues
                print("Locking alembic_version table for migration")
                connection.execute(
                    text("LOCK TABLE alembic_version IN ACCESS EXCLUSIVE MODE")
                )

            now = datetime.datetime.now()
            print("Running migrations at", now)
            context.run_migrations()
            print("Migrations complete at", datetime.datetime.now())
            # Lock is released when transaction ends


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
