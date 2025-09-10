"""Unified Bitbucket rate limiter that works with both httpx and requests libraries."""

import asyncio
import contextlib
import logging
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RateLimitException(Exception):
    """Exception raised when rate limit is exceeded and max retries exhausted"""

    def __init__(self, message: str, key: str = "default", attempts: int = 0) -> None:
        super().__init__(message)
        self.key = key
        self.attempts = attempts


class RateLimitStrategy(str, Enum):
    """Rate limiting strategy options"""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    TOKEN_BUCKET = "token_bucket"


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting"""

    max_requests_per_hour: int = 1000  # Default for authenticated requests
    max_retries: int = 5
    initial_delay: float = 1.0  # Initial delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    backoff_factor: float = 2.0  # Exponential backoff factor
    strategy: RateLimitStrategy = RateLimitStrategy.EXPONENTIAL_BACKOFF
    respect_retry_after: bool = True  # Respect Retry-After header
    min_request_interval: float = 0.1  # Minimum time between requests in seconds


class RateLimitState:
    """Tracks rate limit state for a specific endpoint or token"""

    def __init__(self, config: RateLimitConfig) -> None:
        self.config = config
        self.request_times: deque = deque(maxlen=config.max_requests_per_hour)
        self.lock = Lock()
        self.tokens_remaining: int | None = None
        self.reset_time: datetime | None = None
        self.near_limit: bool = False
        self.last_request_time: float = 0

    def can_make_request(self) -> tuple[bool, float | None]:
        """
        Check if a request can be made now.
        Returns (can_make_request, wait_time_seconds)
        """
        with self.lock:
            now = time.time()

            # Check minimum interval between requests
            time_since_last = now - self.last_request_time
            if time_since_last < self.config.min_request_interval:
                wait_time = self.config.min_request_interval - time_since_last
                return False, wait_time

            # Check if we have rate limit info from headers
            if self.tokens_remaining is not None and self.tokens_remaining <= 0:
                if self.reset_time:
                    wait_time = (self.reset_time - datetime.now()).total_seconds()
                    return False, max(0, wait_time)
                return False, self.config.initial_delay

            # Check rolling window rate limit
            cutoff_time = now - 3600  # 1 hour ago

            # Remove old requests outside the window
            while self.request_times and self.request_times[0] < cutoff_time:
                self.request_times.popleft()

            # Check if we've hit the limit
            if len(self.request_times) >= self.config.max_requests_per_hour:
                # Handle edge case where limit is 0
                if self.config.max_requests_per_hour == 0:
                    return False, 3600.0  # Wait an hour if limit is 0

                # Calculate wait time until the oldest request expires
                if self.request_times:
                    oldest_request = self.request_times[0]
                    wait_time = (oldest_request + 3600) - now
                    return False, max(0, wait_time)
                else:
                    # Edge case: limit reached but no requests in deque
                    return False, self.config.initial_delay

            return True, None

    def record_request(self) -> None:
        """Record that a request was made"""
        with self.lock:
            now = time.time()
            self.request_times.append(now)
            self.last_request_time = now

    def update_from_headers(self, headers: dict[str, str]) -> None:
        """Update rate limit state from response headers"""
        with self.lock:
            # Parse Bitbucket rate limit headers
            if "x-ratelimit-limit" in headers:
                try:
                    limit = int(headers["x-ratelimit-limit"])
                    # Update config if server limit is different
                    if limit != self.config.max_requests_per_hour:
                        logger.info(
                            f"Updating rate limit from {self.config.max_requests_per_hour} to {limit}"
                        )
                        self.config.max_requests_per_hour = limit
                except ValueError:
                    pass

            if "x-ratelimit-remaining" in headers:
                with contextlib.suppress(ValueError):
                    self.tokens_remaining = int(headers["x-ratelimit-remaining"])

            if "x-ratelimit-reset" in headers:
                try:
                    reset_timestamp = int(headers["x-ratelimit-reset"])
                    self.reset_time = datetime.fromtimestamp(reset_timestamp)
                except ValueError:
                    pass

            # Check if we're near the limit
            if "x-ratelimit-nearlimit" in headers:
                self.near_limit = headers["x-ratelimit-nearlimit"].lower() == "true"
            elif (
                self.tokens_remaining is not None
                and self.config.max_requests_per_hour > 0
            ):
                # Consider "near limit" if less than 20% of requests remain
                self.near_limit = self.tokens_remaining < (
                    self.config.max_requests_per_hour * 0.2
                )


class BitbucketRateLimiter:
    """Unified rate limiter for Bitbucket API that works with both httpx and requests"""

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self.config = config or RateLimitConfig()
        self.states: dict[str, RateLimitState] = {}
        self.global_lock = Lock()

    def get_state(self, key: str = "default") -> RateLimitState:
        """Get or create rate limit state for a specific key (e.g., token, endpoint)"""
        with self.global_lock:
            if key not in self.states:
                self.states[key] = RateLimitState(self.config)
            return self.states[key]

    def wait_if_needed(self, key: str = "default") -> float:
        """
        Wait if necessary before making a request.
        Returns the amount of time waited.
        """
        state = self.get_state(key)
        can_proceed, wait_time = state.can_make_request()

        if not can_proceed and wait_time is not None:
            logger.info(
                f"Rate limit reached for {key}, waiting {wait_time:.2f} seconds"
            )
            time.sleep(wait_time)
            return wait_time

        return 0

    def execute_with_retry(
        self,
        func: Callable[[], Any],
        key: str = "default",
        extract_headers: Callable[[Any], dict[str, str]] | None = None,
    ) -> Any:
        """
        Execute a function with rate limiting and retry logic.
        Works with both httpx and requests libraries.

        Args:
            func: The function to execute (should make the API call)
            key: The rate limit key (e.g., token identifier)
            extract_headers: Optional function to extract headers from response
        """
        state = self.get_state(key)
        last_error = None

        for attempt in range(self.config.max_retries):
            # Wait if we need to respect rate limits
            self.wait_if_needed(key)

            try:
                # Record the request
                state.record_request()

                # Execute the function
                result = func()

                # Update rate limit state from response headers if possible
                if extract_headers and result is not None:
                    try:
                        headers = extract_headers(result)
                        state.update_from_headers(headers)

                        # Warn if we're getting close to the limit
                        if state.near_limit:
                            logger.warning(
                                f"Near rate limit for {key}. Tokens remaining: {state.tokens_remaining}"
                            )
                    except Exception as e:
                        logger.debug(f"Could not extract headers from response: {e}")

                # Handle both httpx and requests responses
                if hasattr(result, "raise_for_status"):
                    # This works for both httpx and requests
                    result.raise_for_status()

                return result

            except Exception as e:
                # Check if it's a rate limit error (429)
                status_code = None
                headers = {}

                # Handle httpx.HTTPStatusError
                if hasattr(e, "response") and hasattr(e.response, "status_code"):
                    status_code = e.response.status_code
                    if hasattr(e.response, "headers"):
                        headers = dict(e.response.headers)

                # Handle requests.HTTPError
                elif hasattr(e, "response") and e.response is not None:
                    status_code = getattr(e.response, "status_code", None)
                    if hasattr(e.response, "headers"):
                        headers = dict(e.response.headers)

                if status_code == 429:
                    # Rate limit exceeded
                    last_error = e

                    # Check for Retry-After header
                    retry_after = None
                    if self.config.respect_retry_after:
                        retry_after_header = headers.get("retry-after") or headers.get(
                            "Retry-After"
                        )
                        if retry_after_header:
                            with contextlib.suppress(ValueError):
                                retry_after = float(retry_after_header)

                    # Calculate delay based on strategy
                    if retry_after:
                        delay = retry_after
                    elif self.config.strategy == RateLimitStrategy.EXPONENTIAL_BACKOFF:
                        delay = min(
                            self.config.initial_delay
                            * (self.config.backoff_factor**attempt),
                            self.config.max_delay,
                        )
                    elif self.config.strategy == RateLimitStrategy.FIXED_DELAY:
                        delay = self.config.initial_delay
                    else:  # TOKEN_BUCKET
                        # For token bucket, wait until we have tokens
                        can_proceed, wait_time = state.can_make_request()
                        delay = wait_time or self.config.initial_delay

                    logger.warning(
                        f"Rate limit hit for {key} (attempt {attempt + 1}/{self.config.max_retries}). "
                        f"Waiting {delay:.2f} seconds before retry."
                    )

                    # Update state from error response headers
                    state.update_from_headers(headers)

                    time.sleep(delay)
                    continue

                elif status_code and 400 <= status_code < 500 and status_code != 429:
                    # Client error (not rate limit), don't retry
                    raise

                elif attempt < self.config.max_retries - 1:
                    # Server error or other issue, retry with backoff
                    delay = min(
                        self.config.initial_delay
                        * (self.config.backoff_factor**attempt),
                        self.config.max_delay,
                    )
                    logger.warning(
                        f"Request failed for {key} (attempt {attempt + 1}/{self.config.max_retries}): {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    raise

        # Max retries exceeded
        if last_error:
            logger.error(f"Max retries ({self.config.max_retries}) exceeded for {key}")
            # Check if the last error was a rate limit error
            if (
                hasattr(last_error, "response")
                and getattr(last_error.response, "status_code", None) == 429
            ):
                raise RateLimitException(
                    f"Rate limit exceeded after {self.config.max_retries} attempts for {key}",
                    key=key,
                    attempts=self.config.max_retries,
                ) from last_error
            raise last_error

        raise RateLimitException(
            f"Max retries ({self.config.max_retries}) exceeded without error for {key}",
            key=key,
            attempts=self.config.max_retries,
        )

    async def execute_with_retry_async(
        self,
        func: Callable[[], Any],
        key: str = "default",
        extract_headers: Callable[[Any], dict[str, str]] | None = None,
    ) -> Any:
        """Async version of execute_with_retry"""
        state = self.get_state(key)
        last_error = None

        for attempt in range(self.config.max_retries):
            # Wait if we need to respect rate limits
            can_proceed, wait_time = state.can_make_request()
            if not can_proceed and wait_time is not None:
                logger.info(
                    f"Rate limit reached for {key}, waiting {wait_time:.2f} seconds"
                )
                await asyncio.sleep(wait_time)

            try:
                # Record the request
                state.record_request()

                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func()
                else:
                    result = func()

                # Update rate limit state from response headers if possible
                if extract_headers and result is not None:
                    try:
                        headers = extract_headers(result)
                        state.update_from_headers(headers)

                        # Warn if we're getting close to the limit
                        if state.near_limit:
                            logger.warning(
                                f"Near rate limit for {key}. Tokens remaining: {state.tokens_remaining}"
                            )
                    except Exception as e:
                        logger.debug(f"Could not extract headers from response: {e}")

                # Handle both httpx and requests responses
                if hasattr(result, "raise_for_status"):
                    result.raise_for_status()

                return result

            except Exception as e:
                # Check if it's a rate limit error (429)
                status_code = None
                headers = {}

                # Handle httpx.HTTPStatusError
                if hasattr(e, "response") and hasattr(e.response, "status_code"):
                    status_code = e.response.status_code
                    if hasattr(e.response, "headers"):
                        headers = dict(e.response.headers)

                # Handle requests.HTTPError
                elif hasattr(e, "response") and e.response is not None:
                    status_code = getattr(e.response, "status_code", None)
                    if hasattr(e.response, "headers"):
                        headers = dict(e.response.headers)

                if status_code == 429:
                    # Rate limit exceeded
                    last_error = e

                    # Check for Retry-After header
                    retry_after = None
                    if self.config.respect_retry_after:
                        retry_after_header = headers.get("retry-after") or headers.get(
                            "Retry-After"
                        )
                        if retry_after_header:
                            with contextlib.suppress(ValueError):
                                retry_after = float(retry_after_header)

                    # Calculate delay based on strategy
                    if retry_after:
                        delay = retry_after
                    elif self.config.strategy == RateLimitStrategy.EXPONENTIAL_BACKOFF:
                        delay = min(
                            self.config.initial_delay
                            * (self.config.backoff_factor**attempt),
                            self.config.max_delay,
                        )
                    elif self.config.strategy == RateLimitStrategy.FIXED_DELAY:
                        delay = self.config.initial_delay
                    else:  # TOKEN_BUCKET
                        # For token bucket, wait until we have tokens
                        can_proceed, wait_time = state.can_make_request()
                        delay = wait_time or self.config.initial_delay

                    logger.warning(
                        f"Rate limit hit for {key} (attempt {attempt + 1}/{self.config.max_retries}). "
                        f"Waiting {delay:.2f} seconds before retry."
                    )

                    # Update state from error response headers
                    state.update_from_headers(headers)

                    await asyncio.sleep(delay)
                    continue

                elif status_code and 400 <= status_code < 500 and status_code != 429:
                    # Client error (not rate limit), don't retry
                    raise

                elif attempt < self.config.max_retries - 1:
                    # Server error or other issue, retry with backoff
                    delay = min(
                        self.config.initial_delay
                        * (self.config.backoff_factor**attempt),
                        self.config.max_delay,
                    )
                    logger.warning(
                        f"Request failed for {key} (attempt {attempt + 1}/{self.config.max_retries}): {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    raise

        # Max retries exceeded
        if last_error:
            logger.error(f"Max retries ({self.config.max_retries}) exceeded for {key}")
            # Check if the last error was a rate limit error
            if (
                hasattr(last_error, "response")
                and getattr(last_error.response, "status_code", None) == 429
            ):
                raise RateLimitException(
                    f"Rate limit exceeded after {self.config.max_retries} attempts for {key}",
                    key=key,
                    attempts=self.config.max_retries,
                ) from last_error
            raise last_error

        raise RateLimitException(
            f"Max retries ({self.config.max_retries}) exceeded without error for {key}",
            key=key,
            attempts=self.config.max_retries,
        )

    def get_stats(self) -> dict[str, dict[str, Any]]:
        """Get current rate limit statistics for monitoring"""
        stats = {}
        with self.global_lock:
            for key, state in self.states.items():
                with state.lock:
                    stats[key] = {
                        "tokens_remaining": state.tokens_remaining,
                        "near_limit": state.near_limit,
                        "reset_time": state.reset_time.isoformat()
                        if state.reset_time
                        else None,
                        "requests_in_window": len(state.request_times),
                        "max_requests": state.config.max_requests_per_hour,
                    }
        return stats


# Create a global instance with default settings for backward compatibility
default_rate_limiter = BitbucketRateLimiter()
