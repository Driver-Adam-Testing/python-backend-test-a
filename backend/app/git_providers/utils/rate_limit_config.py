"""
Rate limiting configuration for Bitbucket API.

This module provides environment-based configuration for rate limiting,
allowing easy adjustment of rate limits without code changes.
"""

import os

from shared.rate_limiting import RateLimitConfig, RateLimitStrategy


def get_bitbucket_rate_limit_config() -> RateLimitConfig:
    """
    Get rate limit configuration for Bitbucket API from environment variables.

    Environment variables:
    - BITBUCKET_RATE_LIMIT_MAX_REQUESTS: Maximum requests per hour (default: 1000)
    - BITBUCKET_RATE_LIMIT_MAX_RETRIES: Maximum retry attempts (default: 5)
    - BITBUCKET_RATE_LIMIT_INITIAL_DELAY: Initial delay in seconds (default: 1.0)
    - BITBUCKET_RATE_LIMIT_MAX_DELAY: Maximum delay in seconds (default: 60.0)
    - BITBUCKET_RATE_LIMIT_BACKOFF_FACTOR: Backoff multiplier (default: 2.0)
    - BITBUCKET_RATE_LIMIT_STRATEGY: Strategy type (default: exponential_backoff)
    - BITBUCKET_RATE_LIMIT_MIN_INTERVAL: Minimum seconds between requests (default: 0.5)
    """

    # Parse environment variables with defaults
    max_requests = int(os.getenv("BITBUCKET_RATE_LIMIT_MAX_REQUESTS", "1000"))
    max_retries = int(os.getenv("BITBUCKET_RATE_LIMIT_MAX_RETRIES", "5"))
    initial_delay = float(os.getenv("BITBUCKET_RATE_LIMIT_INITIAL_DELAY", "1.0"))
    max_delay = float(os.getenv("BITBUCKET_RATE_LIMIT_MAX_DELAY", "60.0"))
    backoff_factor = float(os.getenv("BITBUCKET_RATE_LIMIT_BACKOFF_FACTOR", "2.0"))
    min_interval = float(os.getenv("BITBUCKET_RATE_LIMIT_MIN_INTERVAL", "0.5"))

    # Parse strategy
    strategy_str = os.getenv("BITBUCKET_RATE_LIMIT_STRATEGY", "exponential_backoff")
    strategy_map = {
        "exponential_backoff": RateLimitStrategy.EXPONENTIAL_BACKOFF,
        "fixed_delay": RateLimitStrategy.FIXED_DELAY,
        "token_bucket": RateLimitStrategy.TOKEN_BUCKET,
    }
    strategy = strategy_map.get(strategy_str, RateLimitStrategy.EXPONENTIAL_BACKOFF)

    # Check if we should respect Retry-After headers
    respect_retry_after = (
        os.getenv("BITBUCKET_RATE_LIMIT_RESPECT_RETRY_AFTER", "true").lower() == "true"
    )

    return RateLimitConfig(
        max_requests_per_hour=max_requests,
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        strategy=strategy,
        respect_retry_after=respect_retry_after,
        min_request_interval=min_interval,
    )


def get_scaled_rate_limit(paid_users: int) -> int:
    """
    Calculate scaled rate limit based on number of paid users.

    For Bitbucket Standard/Premium plans with 100+ paid users:
    - Base: 1,000 requests per hour
    - Additional: 10 requests per hour per paid user beyond 100
    - Maximum: 10,000 requests per hour

    Args:
        paid_users: Number of paid users in the organization

    Returns:
        Maximum requests per hour
    """
    if paid_users < 100:
        return 1000  # Base rate limit

    # Calculate scaled limit
    additional_requests = (paid_users - 100) * 10
    scaled_limit = 1000 + additional_requests

    # Cap at maximum
    return min(scaled_limit, 10000)


def get_rate_limit_for_token_type(
    token_type: str, paid_users: int | None = None
) -> RateLimitConfig:
    """
    Get rate limit configuration based on token type and organization size.

    Args:
        token_type: Type of access token (workspace, project, repository)
        paid_users: Optional number of paid users for scaled limits

    Returns:
        Rate limit configuration
    """
    base_config = get_bitbucket_rate_limit_config()

    # Adjust based on token type
    if token_type == "workspace" and paid_users and paid_users >= 100:
        # Workspace tokens may benefit from scaled limits
        base_config.max_requests_per_hour = get_scaled_rate_limit(paid_users)

    return base_config
