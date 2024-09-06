import logging
import random
import time
import traceback
import typing
from functools import wraps


def suppress_logging(func):
    """Decorator to suppress logging messages."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger()
        current_level = logger.getEffectiveLevel()
        logger.setLevel(logging.CRITICAL)

        try:
            return func(*args, **kwargs)
        finally:
            logger.setLevel(current_level)

    return wrapper


def retry_with_exponential_backoff(
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    errors: tuple = (Exception,),
):
    """
    Retry a function with exponential backoff.

    Based on example from: https://platform.openai.com/docs/guides/rate-limits/error-mitigation
    """

    def retry_decorator(func):
        def wrapper(*args, **kwargs) -> typing.Any:
            num_retries = 0
            delay = initial_delay

            # Loop until a successful response or max_retries is hit or an exception is raised
            while True:
                try:
                    return func(*args, **kwargs)

                except errors:
                    exception_str = traceback.format_exc()
                    logging.debug(f"Retrying with exception {exception_str}")

                    num_retries += 1

                    if num_retries > max_retries:
                        raise Exception(
                            f"Maximum number of retries ({max_retries}) exceeded."
                        )

                    delay *= exponential_base * (1 + jitter * random.random())

                    msg = "Retrying '%s' in %d sec with args=%s kwargs=%s"
                    logging.debug(msg, func.__name__, delay, args, kwargs)

                    time.sleep(delay)

                # Raise exceptions for any errors not specified
                except Exception as e:
                    raise e

        return wrapper

    return retry_decorator
