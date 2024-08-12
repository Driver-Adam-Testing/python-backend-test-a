import datetime
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, inspect, pool, text
from sqlalchemy.engine import Connection

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(str(config.config_file_name))

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None

from database.models_v1 import SQLModel as SQLModelV1  # noqa
from database.config import settings  # noqa

target_metadata = SQLModelV1.metadata
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    return str(settings.SQLALCHEMY_DATABASE_URI)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def table_exists(connection: Connection, table_name: str) -> bool:
    inspector = inspect(connection)
    return table_name in inspector.get_table_names()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )

        with context.begin_transaction():
            # We allow bypassing the lock for initial setup purposes when the alembic table doesn't exist.
            if table_exists(connection, "alembic_version"):
                # Since we are using Postgres, we can handle DB migration concurrency with LOCK TABLE so that only
                # one container really applies the migrations.
                # https://github.com/sqlalchemy/alembic/issues/633
                # command.ensure_version(config=context.config)
                print("Locking alembic_version table for migration")
                connection.execute(
                    statement=text(
                        "LOCK TABLE alembic_version IN ACCESS EXCLUSIVE MODE"
                    )
                )
            now = datetime.datetime.now(datetime.UTC)
            print("Running migrations at", now)
            context.run_migrations()
            print("Migrations complete at", datetime.datetime.now(datetime.UTC))
            # lock is released when transaction ends


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
