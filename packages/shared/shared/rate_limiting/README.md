# Unified Rate Limiting for Bitbucket API

This module provides a unified rate limiting solution for Bitbucket API calls that works with both `httpx` and `requests` libraries.

## Features

- **Multiple rate limiting strategies**:
  - Exponential backoff (default)
  - Fixed delay
  - Token bucket

- **Automatic retry logic** with configurable max retries
- **Rate limit header parsing** from Bitbucket API responses
- **Support for both sync and async operations**
- **Works with both `httpx` and `requests` libraries**
- **Per-token rate limit tracking**
- **Configurable via environment variables**

## Installation

The rate limiter is part of the shared package and can be imported from anywhere in the codebase:

```python
from shared.rate_limiting import BitbucketRateLimiter, RateLimitConfig
from shared.rate_limiting.config import get_bitbucket_rate_limit_config
```

## Basic Usage

### Using default configuration

```python
from shared.rate_limiting import BitbucketRateLimiter
from shared.rate_limiting.config import get_bitbucket_rate_limit_config

# Create rate limiter with environment-based configuration
rate_limiter = BitbucketRateLimiter(get_bitbucket_rate_limit_config())

# Use with requests library
import requests

def make_api_call():
    return requests.get(
        "https://api.bitbucket.org/2.0/repositories/workspace/repo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

response = rate_limiter.execute_with_retry(
    make_api_call,
    key=f"token_{access_token[:8]}",  # Use token prefix as rate limit key
    extract_headers=lambda resp: dict(resp.headers)
)
```

### Using with httpx

```python
import httpx

def make_api_call():
    with httpx.Client() as client:
        return client.get(
            "https://api.bitbucket.org/2.0/repositories/workspace/repo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

response = rate_limiter.execute_with_retry(
    make_api_call,
    key=f"token_{access_token[:8]}",
    extract_headers=lambda resp: dict(resp.headers)
)
```

### Async usage

```python
import httpx

async def make_api_call():
    async with httpx.AsyncClient() as client:
        return await client.get(
            "https://api.bitbucket.org/2.0/repositories/workspace/repo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

response = await rate_limiter.execute_with_retry_async(
    make_api_call,
    key=f"token_{access_token[:8]}",
    extract_headers=lambda resp: dict(resp.headers)
)
```

## Configuration

### Environment Variables

The rate limiter can be configured using the following environment variables:

- `BITBUCKET_RATE_LIMIT_PER_HOUR`: Maximum requests per hour (default: 1000)
- `BITBUCKET_RATE_LIMIT_STRATEGY`: Rate limiting strategy (default: "exponential_backoff")
  - Options: "exponential_backoff", "fixed_delay", "token_bucket"
- `BITBUCKET_RATE_LIMIT_MAX_RETRIES`: Maximum number of retry attempts (default: 5)
- `BITBUCKET_RATE_LIMIT_INITIAL_DELAY`: Initial delay in seconds (default: 1.0)
- `BITBUCKET_RATE_LIMIT_MAX_DELAY`: Maximum delay in seconds (default: 60.0)
- `BITBUCKET_RATE_LIMIT_BACKOFF_FACTOR`: Exponential backoff multiplier (default: 2.0)
- `BITBUCKET_RATE_LIMIT_MIN_INTERVAL`: Minimum seconds between requests (default: 0.1)
- `BITBUCKET_RATE_LIMIT_RESPECT_RETRY_AFTER`: Honor Retry-After headers (default: true)

### Programmatic Configuration

```python
from shared.rate_limiting import BitbucketRateLimiter, RateLimitConfig, RateLimitStrategy

config = RateLimitConfig(
    max_requests_per_hour=1000,
    max_retries=5,
    initial_delay=1.0,
    max_delay=60.0,
    backoff_factor=2.0,
    strategy=RateLimitStrategy.EXPONENTIAL_BACKOFF,
    respect_retry_after=True,
    min_request_interval=0.5
)

rate_limiter = BitbucketRateLimiter(config)
```

## Rate Limit Tracking

The rate limiter automatically tracks:
- Number of requests made in the current time window
- Remaining API tokens (from response headers)
- Rate limit reset time
- Near-limit warnings

### Getting Rate Limit Statistics

```python
stats = rate_limiter.get_stats()
print(stats)
# Output:
# {
#     'token_abc12345': {
#         'tokens_remaining': 950,
#         'near_limit': False,
#         'reset_time': '2024-01-01T12:00:00',
#         'requests_in_window': 50,
#         'max_requests': 1000
#     }
# }
```

## Migration from Old Rate Limiters

### From backend rate limiter

Replace:
```python
from app.git_providers.utils.rate_limiter import BitbucketRateLimiter, RateLimitConfig
```

With:
```python
from shared.rate_limiting import BitbucketRateLimiter, RateLimitConfig
```

### From content_services rate limiter

Replace:
```python
from onboarding.bitbucket_rate_limiter import rate_limiter

response = rate_limiter.execute_with_retry(
    lambda: requests.get(url, headers=headers)
)
```

With:
```python
from shared.rate_limiting import BitbucketRateLimiter
from shared.rate_limiting.config import get_bitbucket_rate_limit_config

rate_limiter = BitbucketRateLimiter(get_bitbucket_rate_limit_config())

response = rate_limiter.execute_with_retry(
    lambda: requests.get(url, headers=headers),
    key=f"token_{access_token[:8]}",
    extract_headers=lambda resp: dict(resp.headers)
)
```

## Best Practices

1. **Use unique keys for different access tokens**: This ensures rate limits are tracked separately for each token.
   ```python
   key=f"token_{access_token[:8]}"  # Use first 8 chars of token as identifier
   ```

2. **Always provide header extraction**: This allows the rate limiter to update its state based on API responses.
   ```python
   extract_headers=lambda resp: dict(resp.headers)
   ```

3. **Monitor near-limit warnings**: The rate limiter will log warnings when approaching rate limits.

4. **Use appropriate retry strategies**:
   - `EXPONENTIAL_BACKOFF`: Best for most cases, gradually increases delay
   - `FIXED_DELAY`: Use when you want consistent retry intervals
   - `TOKEN_BUCKET`: Use when you want to maintain a steady request rate

5. **Configure based on your Bitbucket plan**:
   - Free tier: 1,000 requests/hour
   - Standard/Premium with 100+ users: Scaled limits up to 10,000 requests/hour

## Support for Other Git Providers

The module also includes configuration helpers for other git providers:

```python
from shared.rate_limiting.config import get_rate_limit_config_for_provider

# Get configuration for GitHub
github_config = get_rate_limit_config_for_provider("github")

# Get configuration for GitLab
gitlab_config = get_rate_limit_config_for_provider("gitlab")
```

Each provider can have its own environment variables:
- `GITHUB_RATE_LIMIT_*` for GitHub
- `GITLAB_RATE_LIMIT_*` for GitLab
