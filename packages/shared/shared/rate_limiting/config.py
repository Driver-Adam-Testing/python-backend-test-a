"""Configuration utilities for rate limiting."""

import os

from .bitbucket_rate_limiter import RateLimitConfig, RateLimitStrategy


def get_bitbucket_rate_limit_config() -> RateLimitConfig:
    """
    Load Bitbucket rate limit configuration from environment variables.

    Environment variables:
    - BITBUCKET_RATE_LIMIT_PER_HOUR: Max requests per hour (default: 1000)
    - BITBUCKET_RATE_LIMIT_STRATEGY: Strategy to use (default: exponential_backoff)
    - BITBUCKET_RATE_LIMIT_MAX_RETRIES: Max retries (default: 5)
    - BITBUCKET_RATE_LIMIT_INITIAL_DELAY: Initial delay in seconds (default: 1.0)
    - BITBUCKET_RATE_LIMIT_MAX_DELAY: Max delay in seconds (default: 60.0)
    - BITBUCKET_RATE_LIMIT_BACKOFF_FACTOR: Backoff factor (default: 2.0)
    - BITBUCKET_RATE_LIMIT_MIN_INTERVAL: Min interval between requests (default: 0.1)
    """

    # Parse strategy from environment
    strategy_str = os.environ.get(
        "BITBUCKET_RATE_LIMIT_STRATEGY", "exponential_backoff"
    )
    try:
        strategy = RateLimitStrategy(strategy_str)
    except ValueError:
        strategy = RateLimitStrategy.EXPONENTIAL_BACKOFF

    return RateLimitConfig(
        max_requests_per_hour=int(
            os.environ.get("BITBUCKET_RATE_LIMIT_PER_HOUR", "1000")
        ),
        max_retries=int(os.environ.get("BITBUCKET_RATE_LIMIT_MAX_RETRIES", "5")),
        initial_delay=float(
            os.environ.get("BITBUCKET_RATE_LIMIT_INITIAL_DELAY", "1.0")
        ),
        max_delay=float(os.environ.get("BITBUCKET_RATE_LIMIT_MAX_DELAY", "60.0")),
        backoff_factor=float(
            os.environ.get("BITBUCKET_RATE_LIMIT_BACKOFF_FACTOR", "2.0")
        ),
        strategy=strategy,
        respect_retry_after=os.environ.get(
            "BITBUCKET_RATE_LIMIT_RESPECT_RETRY_AFTER", "true"
        ).lower()
        == "true",
        min_request_interval=float(
            os.environ.get("BITBUCKET_RATE_LIMIT_MIN_INTERVAL", "0.1")
        ),
    )


def get_rate_limit_config_for_provider(provider: str) -> RateLimitConfig | None:
    """
    Get rate limit configuration for a specific git provider.

    Args:
        provider: The git provider name (e.g., "bitbucket", "github", "gitlab")

    Returns:
        RateLimitConfig or None if provider not supported
    """
    provider_lower = provider.lower()

    if provider_lower == "bitbucket":
        return get_bitbucket_rate_limit_config()
    elif provider_lower == "github":
        # GitHub has different rate limits
        return RateLimitConfig(
            max_requests_per_hour=int(
                os.environ.get("GITHUB_RATE_LIMIT_PER_HOUR", "5000")
            ),
            max_retries=int(os.environ.get("GITHUB_RATE_LIMIT_MAX_RETRIES", "3")),
            initial_delay=float(
                os.environ.get("GITHUB_RATE_LIMIT_INITIAL_DELAY", "1.0")
            ),
            max_delay=float(os.environ.get("GITHUB_RATE_LIMIT_MAX_DELAY", "60.0")),
            backoff_factor=float(
                os.environ.get("GITHUB_RATE_LIMIT_BACKOFF_FACTOR", "2.0")
            ),
            min_request_interval=float(
                os.environ.get("GITHUB_RATE_LIMIT_MIN_INTERVAL", "0.05")
            ),
        )
    elif provider_lower == "gitlab":
        # GitLab has different rate limits
        return RateLimitConfig(
            max_requests_per_hour=int(
                os.environ.get("GITLAB_RATE_LIMIT_PER_HOUR", "2000")
            ),
            max_retries=int(os.environ.get("GITLAB_RATE_LIMIT_MAX_RETRIES", "3")),
            initial_delay=float(
                os.environ.get("GITLAB_RATE_LIMIT_INITIAL_DELAY", "1.0")
            ),
            max_delay=float(os.environ.get("GITLAB_RATE_LIMIT_MAX_DELAY", "60.0")),
            backoff_factor=float(
                os.environ.get("GITLAB_RATE_LIMIT_BACKOFF_FACTOR", "2.0")
            ),
            min_request_interval=float(
                os.environ.get("GITLAB_RATE_LIMIT_MIN_INTERVAL", "0.1")
            ),
        )
    else:
        return None
