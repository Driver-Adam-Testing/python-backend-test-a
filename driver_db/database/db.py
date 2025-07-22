import ssl
import uuid
import urllib.request
from contextlib import contextmanager
from urllib.parse import parse_qs, urlparse

from database.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Session, create_engine
from logger import logger

external_ip = "nopublic"
try:
    with urllib.request.urlopen('https://ident.me') as response:
        external_ip = response.read().decode('utf8')
except Exception as e:
    logger.info("Could not resolve public ip")

app_name = "pback-" + external_ip
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), pool_size=20, pool_pre_ping=True, connect_args={'application_name':app_name})


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


if settings.ASYNC_DATABASE_URL:

    def parse_db_url(url: str) -> tuple[str, dict[str, str]]:
        """
        Parses a database URL and extracts the connection string without query parameters
        and the connection arguments as a dictionary.

        Args:
            url (str): The full database URL.

        Returns:
            Tuple[str, Dict[str, str]]: A tuple containing the base connection string and
                                        the connection arguments.
        """
        parsed_url = urlparse(url)

        query_params = parse_qs(parsed_url.query)

        connect_args = {k: v[0] for k, v in query_params.items()}

        base_connection_string = (
            f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        )
        return base_connection_string, connect_args

    # Asyncpg doesn't seem to support the url ssl query params as it says it does
    # So we need to manually add them back in with this hacking
    # See
    # https://github.com/MagicStack/asyncpg/issues/737
    # https://magicstack.github.io/asyncpg/current/api/index.html#asyncpg.connection.connect
    ssl_ctx = None
    base_async_url, connect_args = parse_db_url(settings.ASYNC_DATABASE_URL)
    if "sslrootcert" in connect_args:
        ssl_ctx = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH, cafile=connect_args["sslrootcert"]
        )
        ssl_ctx.check_hostname = False  # If True, equivalent to sslmode=verify-full, if False sslmode=verify-ca.

    async_engine = create_async_engine(
        base_async_url,
        echo=False,
        connect_args={
            "ssl": ssl_ctx,
            "statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
            "prepared_statement_cache_size": 0,
            "server_settings": {"application_name":"as" + app_name}
        },  # Disable prepared statements for PgBouncer compatibility,
        # Verify these below are good values
        future=True,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True  
    )


def init_db(session: Session) -> None:
    ...
