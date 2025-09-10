"""Unit tests for BitbucketRateLimiter"""

from datetime import datetime, timedelta
from typing import Any, Never
from unittest.mock import Mock, patch

import pytest

from shared.rate_limiting import (
    BitbucketRateLimiter,
    RateLimitConfig,
    RateLimitException,
    RateLimitState,
    RateLimitStrategy,
)


class TestRateLimitConfig:
    """Test RateLimitConfig model"""

    def test_default_config(self) -> None:
        """Test default configuration values"""
        config = RateLimitConfig()
        assert config.max_requests_per_hour == 1000
        assert config.max_retries == 5
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.strategy == RateLimitStrategy.EXPONENTIAL_BACKOFF
        assert config.respect_retry_after is True
        assert config.min_request_interval == 0.1

    def test_custom_config(self) -> None:
        """Test custom configuration values"""
        config = RateLimitConfig(
            max_requests_per_hour=500,
            max_retries=3,
            initial_delay=2.0,
            max_delay=30.0,
            backoff_factor=1.5,
            strategy=RateLimitStrategy.FIXED_DELAY,
            respect_retry_after=False,
            min_request_interval=0.5,
        )
        assert config.max_requests_per_hour == 500
        assert config.max_retries == 3
        assert config.initial_delay == 2.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 1.5
        assert config.strategy == RateLimitStrategy.FIXED_DELAY
        assert config.respect_retry_after is False
        assert config.min_request_interval == 0.5


class TestRateLimitState:
    """Test RateLimitState tracking"""

    def test_can_make_request_initial_state(self) -> None:
        """Test that initial state allows requests"""
        config = RateLimitConfig(min_request_interval=0)
        state = RateLimitState(config)
        can_proceed, wait_time = state.can_make_request()
        assert can_proceed is True
        assert wait_time is None

    def test_minimum_interval_enforcement(self) -> None:
        """Test minimum interval between requests"""
        config = RateLimitConfig(min_request_interval=1.0)
        state = RateLimitState(config)

        # First request should be allowed
        can_proceed, wait_time = state.can_make_request()
        assert can_proceed is True

        # Record the request
        state.record_request()

        # Immediate second request should be blocked
        can_proceed, wait_time = state.can_make_request()
        assert can_proceed is False
        assert wait_time is not None
        assert 0 < wait_time <= 1.0

    def test_hourly_rate_limit(self) -> None:
        """Test hourly rate limit enforcement"""
        config = RateLimitConfig(max_requests_per_hour=10, min_request_interval=0)
        state = RateLimitState(config)

        # Make 10 requests
        for _ in range(10):
            can_proceed, wait_time = state.can_make_request()
            assert can_proceed is True
            state.record_request()

        # 11th request should be blocked
        can_proceed, wait_time = state.can_make_request()
        assert can_proceed is False
        assert wait_time is not None

    def test_update_from_headers(self) -> None:
        """Test updating state from response headers"""
        config = RateLimitConfig()
        state = RateLimitState(config)

        headers = {
            "x-ratelimit-limit": "500",
            "x-ratelimit-remaining": "450",
            "x-ratelimit-reset": str(
                int((datetime.now() + timedelta(hours=1)).timestamp())
            ),
            "x-ratelimit-nearlimit": "false",
        }

        state.update_from_headers(headers)

        assert state.config.max_requests_per_hour == 500
        assert state.tokens_remaining == 450
        assert state.reset_time is not None
        assert state.near_limit is False

    def test_near_limit_detection(self) -> None:
        """Test automatic near limit detection"""
        config = RateLimitConfig(max_requests_per_hour=100)
        state = RateLimitState(config)

        # Set remaining tokens to 15 (15% of limit)
        headers = {
            "x-ratelimit-remaining": "15",
        }
        state.update_from_headers(headers)

        # Should be considered near limit (< 20%)
        assert state.near_limit is True


class TestBitbucketRateLimiter:
    """Test BitbucketRateLimiter main functionality"""

    def test_initialization(self) -> None:
        """Test rate limiter initialization"""
        config = RateLimitConfig()
        limiter = BitbucketRateLimiter(config)
        assert limiter.config == config
        assert len(limiter.states) == 0

    def test_get_state_creates_new(self) -> None:
        """Test that get_state creates new state if not exists"""
        limiter = BitbucketRateLimiter()
        state1 = limiter.get_state("token1")
        state2 = limiter.get_state("token2")

        assert state1 != state2
        assert len(limiter.states) == 2
        assert "token1" in limiter.states
        assert "token2" in limiter.states

    def test_get_state_returns_existing(self) -> None:
        """Test that get_state returns existing state"""
        limiter = BitbucketRateLimiter()
        state1 = limiter.get_state("token1")
        state2 = limiter.get_state("token1")

        assert state1 is state2
        assert len(limiter.states) == 1

    @patch("time.sleep")
    def test_wait_if_needed(self, mock_sleep: Mock) -> None:
        """Test wait_if_needed functionality"""
        config = RateLimitConfig(max_requests_per_hour=1, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        # First request should not wait
        wait_time = limiter.wait_if_needed("test")
        assert wait_time == 0
        mock_sleep.assert_not_called()

        # Record a request
        state = limiter.get_state("test")
        state.record_request()

        # Second request should wait
        wait_time = limiter.wait_if_needed("test")
        assert wait_time > 0
        mock_sleep.assert_called_once()

    def test_execute_with_retry_success(self) -> None:
        """Test successful execution without retry"""
        limiter = BitbucketRateLimiter()

        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.headers = {}

        mock_func = Mock(return_value=mock_response)

        result = limiter.execute_with_retry(mock_func)

        assert result == mock_response
        assert mock_func.call_count == 1

    @patch("time.sleep")
    def test_execute_with_retry_rate_limit(self, mock_sleep: Mock) -> None:
        """Test retry on rate limit error"""
        config = RateLimitConfig(
            max_retries=2, initial_delay=1.0, min_request_interval=0
        )
        limiter = BitbucketRateLimiter(config)

        # Mock rate limit error then success
        mock_error = Mock()
        mock_error.response = Mock()
        mock_error.response.status_code = 429
        mock_error.response.headers = {}

        mock_success = Mock()
        mock_success.raise_for_status = Mock()
        mock_success.headers = {}

        mock_func = Mock(side_effect=[mock_error, mock_success])

        # Need to make raise_for_status raise the error on first call
        def raise_rate_limit() -> Never:
            raise mock_error

        mock_error.raise_for_status = raise_rate_limit

        result = limiter.execute_with_retry(mock_func)

        assert result == mock_success
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    @patch("time.sleep")
    def test_execute_with_retry_exponential_backoff(self, mock_sleep: Mock) -> None:
        """Test exponential backoff strategy"""
        config = RateLimitConfig(
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            strategy=RateLimitStrategy.EXPONENTIAL_BACKOFF,
            min_request_interval=0,
        )
        limiter = BitbucketRateLimiter(config)

        # Mock multiple rate limit errors
        class RateLimitError(Exception):
            def __init__(self) -> None:
                self.response = Mock()
                self.response.status_code = 429
                self.response.headers = {}

        # Create multiple instances since each will be raised once
        errors = [RateLimitError(), RateLimitError(), RateLimitError()]
        mock_func = Mock(side_effect=errors)

        with pytest.raises(RateLimitException):
            limiter.execute_with_retry(mock_func)

        # Check exponential backoff delays
        assert mock_sleep.call_count == 3  # Sleeps after each of the 3 429 errors
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert delays[0] == 1.0  # First delay
        assert delays[1] == 2.0  # Second delay (1.0 * 2)
        assert delays[2] == 4.0  # Third delay (2.0 * 2)

    @patch("time.sleep")
    def test_execute_with_retry_respect_retry_after(self, mock_sleep: Mock) -> None:
        """Test respecting Retry-After header"""
        config = RateLimitConfig(respect_retry_after=True, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        # Create proper exception with Retry-After
        class RateLimitError(Exception):
            def __init__(self) -> None:
                self.response = Mock()
                self.response.status_code = 429
                self.response.headers = {"Retry-After": "5"}

        call_count = 0

        def mock_func() -> Mock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError()
            else:
                mock_success = Mock()
                mock_success.raise_for_status = Mock()
                mock_success.headers = {}
                return mock_success

        limiter.execute_with_retry(mock_func)

        assert call_count == 2
        mock_sleep.assert_called_once_with(5.0)

    def test_execute_with_retry_client_error(self) -> None:
        """Test that client errors are not retried"""
        limiter = BitbucketRateLimiter()

        # Create a proper exception class
        class ClientError(Exception):
            def __init__(self) -> None:
                self.response = Mock()
                self.response.status_code = 400
                self.response.headers = {}

        mock_func = Mock(side_effect=ClientError())

        with pytest.raises(ClientError):
            limiter.execute_with_retry(mock_func)

        # Should only be called once (no retry)
        assert mock_func.call_count == 1

    def test_execute_with_retry_extract_headers(self) -> None:
        """Test header extraction functionality"""
        limiter = BitbucketRateLimiter()

        # Mock response with headers
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.headers = {
            "x-ratelimit-remaining": "950",
            "x-ratelimit-limit": "1000",
        }

        mock_func = Mock(return_value=mock_response)

        def extract_headers(resp: Any) -> dict[str, str]:
            return dict(resp.headers)

        result = limiter.execute_with_retry(
            mock_func, key="test_token", extract_headers=extract_headers
        )

        assert result == mock_response

        # Check that state was updated
        state = limiter.get_state("test_token")
        assert state.tokens_remaining == 950
        assert state.config.max_requests_per_hour == 1000

    @pytest.mark.asyncio
    async def test_execute_with_retry_async_success(self) -> None:
        """Test async execution success"""
        limiter = BitbucketRateLimiter()

        # Mock successful async response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.headers = {}

        async def mock_func() -> Mock:
            return mock_response

        result = await limiter.execute_with_retry_async(mock_func)

        assert result == mock_response

    @pytest.mark.asyncio
    @patch("asyncio.sleep")
    async def test_execute_with_retry_async_rate_limit(self, mock_sleep: Mock) -> None:
        """Test async retry on rate limit"""
        config = RateLimitConfig(max_retries=2, initial_delay=1.0)
        limiter = BitbucketRateLimiter(config)

        # Mock rate limit error then success
        mock_error = Mock()
        mock_error.response = Mock()
        mock_error.response.status_code = 429
        mock_error.response.headers = {}

        mock_success = Mock()
        mock_success.raise_for_status = Mock()
        mock_success.headers = {}

        call_count = 0

        async def mock_func() -> Mock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:

                def raise_rate_limit() -> Never:
                    raise mock_error

                mock_error.raise_for_status = raise_rate_limit
                return mock_error
            else:
                return mock_success

        result = await limiter.execute_with_retry_async(mock_func)

        assert result == mock_success
        assert call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    def test_get_stats(self) -> None:
        """Test statistics retrieval"""
        limiter = BitbucketRateLimiter()

        # Create some states with different values
        state1 = limiter.get_state("token1")
        state1.tokens_remaining = 500
        state1.near_limit = False

        state2 = limiter.get_state("token2")
        state2.tokens_remaining = 50
        state2.near_limit = True
        state2.reset_time = datetime.now() + timedelta(hours=1)

        stats = limiter.get_stats()

        assert "token1" in stats
        assert "token2" in stats

        assert stats["token1"]["tokens_remaining"] == 500
        assert stats["token1"]["near_limit"] is False
        assert stats["token1"]["reset_time"] is None

        assert stats["token2"]["tokens_remaining"] == 50
        assert stats["token2"]["near_limit"] is True
        assert stats["token2"]["reset_time"] is not None


class TestRequestsCompatibility:
    """Test compatibility with requests library"""

    def test_requests_response_handling(self) -> None:
        """Test handling of requests.Response objects"""
        import requests

        limiter = BitbucketRateLimiter()

        # Mock requests response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {"x-ratelimit-remaining": "999"}
        mock_response.raise_for_status = Mock()

        mock_func = Mock(return_value=mock_response)

        result = limiter.execute_with_retry(
            mock_func, extract_headers=lambda resp: dict(resp.headers)
        )

        assert result == mock_response
        mock_response.raise_for_status.assert_called_once()

    @patch("time.sleep")
    def test_requests_http_error_429(self, mock_sleep: Mock) -> None:
        """Test handling of requests.HTTPError with 429 status"""
        import requests

        config = RateLimitConfig(max_retries=2, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        # Create HTTPError with 429 status
        mock_response_429 = Mock(spec=requests.Response)
        mock_response_429.status_code = 429
        mock_response_429.headers = {}

        error_429 = requests.HTTPError(response=mock_response_429)

        # Success response
        mock_success = Mock(spec=requests.Response)
        mock_success.raise_for_status = Mock()
        mock_success.headers = {}

        # First call raises 429, second succeeds
        mock_func = Mock(side_effect=[error_429, mock_success])

        result = limiter.execute_with_retry(mock_func)

        assert result == mock_success
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    def test_rate_limit_exception_raised_when_max_retries_exceeded(
        self, mock_sleep: Mock
    ) -> None:
        """Test that RateLimitException is raised when max retries are exceeded for 429 errors"""
        import requests

        config = RateLimitConfig(max_retries=3, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        # Create HTTPError with 429 status
        mock_response_429 = Mock(spec=requests.Response)
        mock_response_429.status_code = 429
        mock_response_429.headers = {}

        error_429 = requests.HTTPError(response=mock_response_429)

        # All calls raise 429 error
        mock_func = Mock(side_effect=[error_429, error_429, error_429])

        # Should raise RateLimitException after max retries
        with pytest.raises(RateLimitException) as exc_info:
            limiter.execute_with_retry(mock_func, key="test_key")

        # Verify exception details
        assert "Rate limit exceeded after 3 attempts" in str(exc_info.value)
        assert exc_info.value.key == "test_key"
        assert exc_info.value.attempts == 3
        assert mock_func.call_count == 3
        # Should have slept after each failed attempt (3 times for 3 attempts with 429)
        assert mock_sleep.call_count == 3


class TestHttpxCompatibility:
    """Test compatibility with httpx library"""

    def test_httpx_response_handling(self) -> None:
        """Test handling of httpx.Response objects"""
        # Mock httpx response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"x-ratelimit-remaining": "999"}
        mock_response.raise_for_status = Mock()

        limiter = BitbucketRateLimiter()
        mock_func = Mock(return_value=mock_response)

        result = limiter.execute_with_retry(
            mock_func, extract_headers=lambda resp: dict(resp.headers)
        )

        assert result == mock_response
        mock_response.raise_for_status.assert_called_once()

    @patch("time.sleep")
    def test_httpx_status_error_429(self, mock_sleep: Mock) -> None:
        """Test handling of httpx.HTTPStatusError with 429 status"""
        config = RateLimitConfig(max_retries=2, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        # Mock HTTPStatusError with 429
        mock_error = Mock()
        mock_error.response = Mock()
        mock_error.response.status_code = 429
        mock_error.response.headers = {}

        # Success response
        mock_success = Mock()
        mock_success.raise_for_status = Mock()
        mock_success.headers = {}

        # First call raises error, second succeeds
        mock_func = Mock(side_effect=[mock_error, mock_success])

        def raise_rate_limit() -> Never:
            raise mock_error

        mock_error.raise_for_status = raise_rate_limit

        result = limiter.execute_with_retry(mock_func)

        assert result == mock_success
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once()
