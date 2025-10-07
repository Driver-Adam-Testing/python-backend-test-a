import logging
import random
import threading
import time
import traceback
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import requests
from auth0.exceptions import Auth0Error

logger = logging.getLogger(__name__)

RET_TYPE = TypeVar("RET_TYPE")

# Shared state across all Auth0Service instances for rate limit coordination
_auth0_rate_limit_state = {
    "reset_time": 0.0,  # When rate limit resets (epoch seconds)
    "lock": threading.Lock(),
}


def retry_with_auth0_rate_limiting(
    initial_delay: float = 1,
    exponential_base: float = 2,
    max_retries: int = 3,
    jitter_max_seconds: float = 5.0,
) -> Callable:
    """
    Auth0-specific retry decorator with global rate limit awareness.

    Handles:
    - 429 rate limits: Sleep until X-RateLimit-Reset + random jitter
    - Network/5xx errors: Exponential backoff
    - Thread-safe for concurrent invocations

    Args:
        initial_delay: Starting delay for exponential backoff (seconds)
        exponential_base: Multiplier for exponential backoff
        max_retries: Maximum number of retry attempts
        jitter_max_seconds: Maximum random delay after rate limit reset
    """

    def retry_decorator(func: Callable[..., RET_TYPE]) -> Callable[..., RET_TYPE]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> RET_TYPE:
            num_retries = 0
            delay = initial_delay

            while True:
                try:
                    # Check if we're currently rate limited globally
                    with _auth0_rate_limit_state["lock"]:
                        current_time = time.time()
                        if _auth0_rate_limit_state["reset_time"] > current_time:
                            # We're still in a rate limit period, wait it out
                            wait_time = (
                                _auth0_rate_limit_state["reset_time"] - current_time
                            )
                            jitter = random.uniform(0, jitter_max_seconds)
                            total_wait = wait_time + jitter

                            logger.info(
                                f"Auth0 rate limit active, waiting {total_wait:.2f}s "
                                f"(reset in {wait_time:.2f}s + {jitter:.2f}s jitter)"
                            )
                            time.sleep(total_wait)

                    # Attempt the function call
                    return func(*args, **kwargs)

                except requests.exceptions.HTTPError as e:
                    if e.response is not None and e.response.status_code == 429:
                        # Rate limit hit - update global state
                        reset_header = e.response.headers.get("X-RateLimit-Reset", "1")
                        try:
                            reset_time = float(reset_header)
                        except ValueError:
                            # If header is not a valid number, default to 1 second from now
                            reset_time = time.time() + 1

                        with _auth0_rate_limit_state["lock"]:
                            # Update global reset time (take max in case multiple threads hit rate limit)
                            _auth0_rate_limit_state["reset_time"] = max(
                                _auth0_rate_limit_state["reset_time"], reset_time
                            )

                        logger.warning(
                            f"Auth0 rate limit hit in {func.__name__}, "
                            f"reset at {reset_time} ({reset_time - time.time():.2f}s from now)"
                        )

                        num_retries += 1
                        if num_retries > max_retries:
                            logger.error(
                                f"Max retries ({max_retries}) exceeded for {func.__name__} due to rate limiting"
                            )
                            raise Exception(
                                f"Auth0 rate limit exceeded after {max_retries} retries"
                            ) from e

                        # Wait for rate limit to reset + jitter
                        wait_time = max(reset_time - time.time(), 0)
                        jitter = random.uniform(0, jitter_max_seconds)
                        total_wait = wait_time + jitter

                        logger.info(f"Retrying {func.__name__} in {total_wait:.2f}s")
                        time.sleep(total_wait)

                    elif e.response is not None and e.response.status_code >= 500:
                        # Server error - use exponential backoff
                        num_retries += 1
                        if num_retries > max_retries:
                            logger.error(
                                f"Max retries ({max_retries}) exceeded for {func.__name__} "
                                f"due to server error {e.response.status_code}"
                            )
                            raise Exception(
                                f"Auth0 server error after {max_retries} retries"
                            ) from e

                        jitter = random.uniform(0, delay * 0.1)  # 10% jitter
                        total_delay = delay + jitter

                        logger.warning(
                            f"Auth0 server error {e.response.status_code} in {func.__name__}, "
                            f"retrying in {total_delay:.2f}s (attempt {num_retries}/{max_retries})"
                        )

                        time.sleep(total_delay)
                        delay *= exponential_base

                    else:
                        # Client error (4xx) or other HTTP error - don't retry
                        logger.error(
                            f"Non-retryable HTTP error in {func.__name__}: {e.response.status_code if e.response else 'unknown'}"
                        )
                        raise

                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException,
                ) as e:
                    # Network errors - use exponential backoff
                    num_retries += 1
                    if num_retries > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__} "
                            f"due to network error: {type(e).__name__}"
                        )
                        raise Exception(
                            f"Auth0 network error after {max_retries} retries"
                        ) from e

                    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
                    total_delay = delay + jitter

                    logger.warning(
                        f"Network error in {func.__name__}: {type(e).__name__}, "
                        f"retrying in {total_delay:.2f}s (attempt {num_retries}/{max_retries})"
                    )

                    time.sleep(total_delay)
                    delay *= exponential_base

                except Auth0Error as e:
                    # Auth0 SDK specific errors
                    status_code = getattr(e, "status_code", None)

                    if status_code == 429:
                        # Handle Auth0 SDK rate limit similar to requests
                        num_retries += 1
                        if num_retries > max_retries:
                            logger.error(
                                f"Max retries ({max_retries}) exceeded for {func.__name__} due to Auth0 rate limiting"
                            )
                            raise Exception(
                                f"Auth0 rate limit exceeded after {max_retries} retries"
                            ) from e

                        # Use default wait time since Auth0Error may not have headers
                        wait_time = delay
                        jitter = random.uniform(0, jitter_max_seconds)
                        total_wait = wait_time + jitter

                        logger.warning(
                            f"Auth0 SDK rate limit in {func.__name__}, "
                            f"retrying in {total_wait:.2f}s"
                        )
                        time.sleep(total_wait)

                    elif status_code and status_code >= 500:
                        # Server error
                        num_retries += 1
                        if num_retries > max_retries:
                            logger.error(
                                f"Max retries ({max_retries}) exceeded for {func.__name__} due to Auth0 server error"
                            )
                            raise Exception(
                                f"Auth0 server error after {max_retries} retries"
                            ) from e

                        jitter = random.uniform(0, delay * 0.1)
                        total_delay = delay + jitter
                        time.sleep(total_delay)
                        delay *= exponential_base

                    else:
                        # Client error or other Auth0 error - don't retry
                        logger.error(
                            f"Non-retryable Auth0 error in {func.__name__}: {e}"
                        )
                        raise

                except Exception as e:
                    # Unexpected errors - log and re-raise without retry
                    logger.error(
                        f"Unexpected error in {func.__name__}: {type(e).__name__}: {e}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    raise

        return wrapper

    return retry_decorator


def retry_auth0_call(
    func: Callable[[], RET_TYPE],
    max_retries: int = 3,
    jitter_max_seconds: float = 5.0,
) -> RET_TYPE:
    """
    Helper function to wrap Auth0 API calls with retry logic.

    Usage:
        user_data = retry_auth0_call(lambda: auth0_service.get_user_profile(user_id))
        org_data = retry_auth0_call(lambda: auth0_service.get_organization(org_id))

    Args:
        func: Lambda or callable that makes the Auth0 API call
        max_retries: Maximum number of retry attempts
        jitter_max_seconds: Maximum random delay after rate limit reset

    Returns:
        Result of the Auth0 API call

    Raises:
        Exception: If max retries exceeded or non-retryable error occurs
    """
    decorated_func = retry_with_auth0_rate_limiting(
        max_retries=max_retries, jitter_max_seconds=jitter_max_seconds
    )(func)

    return decorated_func()


def reset_auth0_rate_limit_state() -> None:
    """
    Reset the global rate limit state. Useful for testing or manual intervention.
    """
    with _auth0_rate_limit_state["lock"]:
        _auth0_rate_limit_state["reset_time"] = 0.0
    logger.info("Auth0 rate limit state reset")


def get_auth0_rate_limit_status() -> dict[str, Any]:
    """
    Get current rate limit status for monitoring/debugging.
    """
    with _auth0_rate_limit_state["lock"]:
        current_time = time.time()
        reset_time = _auth0_rate_limit_state["reset_time"]

        return {
            "currently_rate_limited": reset_time > current_time,
            "reset_time": reset_time,
            "seconds_until_reset": max(0, reset_time - current_time),
        }
