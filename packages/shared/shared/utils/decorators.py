import asyncio
import logging
import random
import time
import traceback
import typing
from collections.abc import Callable
from functools import wraps
from threading import Lock
from typing import Any

RET_TYPE = typing.TypeVar("RET_TYPE")

logger = logging.getLogger(__name__)


def expiring_cache(duration_sec: int) -> Callable:
    """
    Cache the result of a function with a specified cache invalidation time
    Thread-safe implementation using a Lock.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache: dict[str, Any] = {"value": None, "expires_at": 0}
        lock = Lock()

        def wrapped(*args: object, **kwargs: object) -> Any:
            nonlocal cache
            current_time = time.time()

            with lock:
                if cache["expires_at"] < current_time:
                    logger.info(f"Cache expired, calling function {func.__name__}")
                    cache["value"] = func(*args, **kwargs)
                    cache["expires_at"] = current_time + duration_sec
                return cache["value"]

        def clear_cache() -> None:
            with lock:
                cache.update({"value": None, "expires_at": 0})

        wrapped.clear_cache = clear_cache
        return wrapped

    return decorator


def suppress_logging(func: typing.Callable[..., RET_TYPE]) -> typing.Callable:
    """Decorator to suppress logging messages."""

    @wraps(func)
    def wrapper(*args: tuple, **kwargs: dict) -> RET_TYPE:
        logger = logging.getLogger()
        current_level = logger.getEffectiveLevel()
        logger.setLevel(logging.CRITICAL)

        try:
            return func(*args, **kwargs)
        finally:
            logger.setLevel(current_level)

    return wrapper


def async_retry_with_exponential_backoff(
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    errors: tuple = (Exception,),
) -> typing.Callable:
    """
    Retry a function with exponential backoff.

    Based on example from: https://platform.openai.com/docs/guides/rate-limits/error-mitigation
    """

    def retry_decorator(func: typing.Callable[..., RET_TYPE]) -> typing.Callable:
        async def wrapper(*args: tuple, **kwargs: dict) -> RET_TYPE:
            num_retries = 0
            delay = initial_delay

            # Loop until a successful response or max_retries is hit or an exception is raised
            while True:
                try:
                    return await func(*args, **kwargs)

                except errors as e:
                    exception_str = traceback.format_exc()
                    print(f"Retrying with exception {exception_str}")

                    num_retries += 1

                    if num_retries > max_retries:
                        raise Exception(
                            f"Maximum number of retries ({max_retries}) exceeded."
                        ) from e

                    delay *= exponential_base * (1 + jitter * random.random())

                    print(
                        f"Retrying {func.__name__} in {delay} sec with args={args} kwargs={kwargs}"
                    )

                    await asyncio.sleep(delay)

                # Raise exceptions for any errors not specified
                except Exception as e:
                    raise e

        return wrapper

    return retry_decorator


def retry_with_exponential_backoff(
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    errors: tuple = (Exception,),
) -> typing.Callable:
    """
    Retry a function with exponential backoff.

    Based on example from: https://platform.openai.com/docs/guides/rate-limits/error-mitigation
    """

    def retry_decorator(func: typing.Callable[..., RET_TYPE]) -> typing.Callable:
        def wrapper(*args: tuple, **kwargs: dict) -> RET_TYPE:
            num_retries = 0
            delay = initial_delay

            # Loop until a successful response or max_retries is hit or an exception is raised
            while True:
                try:
                    return func(*args, **kwargs)

                except errors as e:
                    exception_str = traceback.format_exc()
                    logging.debug(f"Retrying with exception {exception_str}")

                    num_retries += 1

                    if num_retries > max_retries:
                        raise Exception(
                            f"Maximum number of retries ({max_retries}) exceeded."
                        ) from e

                    delay *= exponential_base * (1 + jitter * random.random())

                    msg = "Retrying '%s' in %d sec with args=%s kwargs=%s"
                    logging.debug(msg, func.__name__, delay, args, kwargs)

                    time.sleep(delay)

                # Raise exceptions for any errors not specified
                except Exception as e:
                    raise e

        return wrapper

    return retry_decorator
