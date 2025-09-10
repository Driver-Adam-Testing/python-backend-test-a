"""Integration tests for rate limiter with realistic scenarios"""

import asyncio
import contextlib
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Never
from unittest.mock import Mock, patch

import pytest

from shared.rate_limiting import (
    BitbucketRateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
)


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @patch("time.sleep")
    def test_bulk_repository_fetch(self, mock_sleep: Mock) -> None:
        """Test fetching multiple repositories with rate limiting"""
        config = RateLimitConfig(
            max_requests_per_hour=10,  # Low limit for testing
            min_request_interval=0.1,
        )
        limiter = BitbucketRateLimiter(config)

        # Simulate fetching 15 repositories (exceeds limit)
        successful_calls = []

        for i in range(15):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.headers = {
                "x-ratelimit-remaining": str(max(0, 10 - i - 1)),
                "x-ratelimit-limit": "10",
            }

            def make_request(repo_id: int = i, response: Any = mock_response) -> Any:
                successful_calls.append(repo_id)
                return response

            if i < 10:
                # First 10 should succeed
                result = limiter.execute_with_retry(
                    make_request,
                    key="workspace_token",
                    extract_headers=lambda resp: dict(resp.headers),
                )
                assert result == mock_response
            else:
                # 11th request should be rate limited
                state = limiter.get_state("workspace_token")
                can_proceed, wait_time = state.can_make_request()
                assert can_proceed is False
                break

        assert len(successful_calls) == 10

    def test_multiple_access_tokens(self) -> None:
        """Test using multiple access tokens with separate rate limits"""
        config = RateLimitConfig(max_requests_per_hour=5, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        tokens = ["token_a", "token_b", "token_c"]
        request_counts = {token: 0 for token in tokens}

        # Make requests with different tokens
        for _ in range(15):  # 5 requests per token
            for token in tokens:
                state = limiter.get_state(token)
                can_proceed, _ = state.can_make_request()

                if can_proceed:
                    state.record_request()
                    request_counts[token] += 1

        # Each token should have made exactly 5 requests
        for token in tokens:
            assert request_counts[token] == 5

            # And should now be rate limited
            state = limiter.get_state(token)
            can_proceed, _ = state.can_make_request()
            assert can_proceed is False

    @patch("time.sleep")
    def test_webhook_event_burst(self, mock_sleep: Mock) -> None:
        """Test handling webhook event bursts with rate limiting"""
        config = RateLimitConfig(
            max_requests_per_hour=100,
            min_request_interval=0.05,  # 50ms between requests
            strategy=RateLimitStrategy.TOKEN_BUCKET,
        )
        limiter = BitbucketRateLimiter(config)

        # Simulate 20 webhook events arriving simultaneously
        events_processed = []

        def process_event(event_id: int) -> Any:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.headers = {}

            result = limiter.execute_with_retry(
                lambda: mock_response, key="webhook_token"
            )
            events_processed.append(event_id)
            return result

        # Process events
        for i in range(20):
            process_event(i)

        # All events should be processed (rate limited but not blocked)
        assert len(events_processed) == 20

        # Sleep should have been called for min_request_interval
        assert mock_sleep.call_count > 0

    @pytest.mark.asyncio
    async def test_concurrent_async_requests(self) -> None:
        """Test concurrent async requests with rate limiting"""
        config = RateLimitConfig(max_requests_per_hour=10, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        successful_requests = []

        async def make_request(request_id: int) -> Any:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.headers = {}

            try:
                result = await limiter.execute_with_retry_async(
                    lambda: mock_response, key="async_token"
                )
                successful_requests.append(request_id)
                return result
            except Exception:
                return None

        # Launch 15 concurrent requests
        tasks = [make_request(i) for i in range(15)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Only 10 should succeed due to rate limit
        assert (
            len([r for r in results if r is not None and not isinstance(r, Exception)])
            <= 10
        )

    def test_rate_limit_recovery(self) -> None:
        """Test rate limit recovery over time"""
        config = RateLimitConfig(max_requests_per_hour=10, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        # Use up all requests
        state = limiter.get_state("recovery_token")
        for _ in range(10):
            state.record_request()

        # Should be rate limited
        can_proceed, wait_time = state.can_make_request()
        assert can_proceed is False

        # Simulate time passing (manipulate request_times directly)
        with state.lock:
            # Clear old requests to simulate hour passing
            state.request_times.clear()

        # Should now be able to make requests again
        can_proceed, wait_time = state.can_make_request()
        assert can_proceed is True

    @patch("time.sleep")
    def test_error_handling_with_retry(self, mock_sleep: Mock) -> None:
        """Test error handling and retry logic"""
        config = RateLimitConfig(
            max_retries=3,
            initial_delay=0.5,
            strategy=RateLimitStrategy.EXPONENTIAL_BACKOFF,
            min_request_interval=0,
        )
        limiter = BitbucketRateLimiter(config)

        call_count = 0

        def flaky_request() -> Any:
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                # Fail first two attempts with rate limit
                error = Mock()
                error.response = Mock()
                error.response.status_code = 429
                error.response.headers = {}

                def raise_error() -> Never:
                    raise error

                error.raise_for_status = raise_error
                return error
            else:
                # Succeed on third attempt
                success = Mock()
                success.raise_for_status = Mock()
                success.headers = {"x-ratelimit-remaining": "999"}
                return success

        result = limiter.execute_with_retry(
            flaky_request, extract_headers=lambda resp: dict(resp.headers)
        )

        assert call_count == 3
        assert result.headers["x-ratelimit-remaining"] == "999"

        # Check backoff delays
        assert mock_sleep.call_count == 2
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert delays[0] == 0.5  # First retry
        assert delays[1] == 1.0  # Second retry (0.5 * 2)


class TestConcurrentAccessPatterns:
    """Test concurrent access patterns and thread safety"""

    def test_thread_safety(self) -> None:
        """Test thread safety with concurrent requests"""
        config = RateLimitConfig(max_requests_per_hour=100, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        successful_requests = []
        import threading

        lock = threading.Lock()  # Use real lock for thread-safe list append

        def make_request(thread_id: int) -> bool:
            state = limiter.get_state("shared_token")
            can_proceed, _ = state.can_make_request()

            if can_proceed:
                state.record_request()
                with lock:
                    successful_requests.append(thread_id)
                return True
            return False

        # Run requests from multiple threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(150)]
            results = [f.result() for f in futures]

        # Should have exactly 100 successful requests (rate limit)
        successful_count = sum(1 for r in results if r)
        assert successful_count == 100

    def test_token_isolation(self) -> None:
        """Test that different tokens are properly isolated"""
        limiter = BitbucketRateLimiter()

        # Create states for different tokens
        state1 = limiter.get_state("token1")
        state2 = limiter.get_state("token2")

        # Use up rate limit for token1
        for _ in range(1000):
            state1.record_request()

        # token1 should be rate limited
        can_proceed1, _ = state1.can_make_request()
        assert can_proceed1 is False

        # token2 should still be able to make requests
        can_proceed2, _ = state2.can_make_request()
        assert can_proceed2 is True

    def test_header_update_race_condition(self) -> None:
        """Test header updates don't cause race conditions"""
        config = RateLimitConfig()
        limiter = BitbucketRateLimiter(config)

        def update_headers(thread_id: int) -> int | None:
            state = limiter.get_state("race_token")
            headers = {
                "x-ratelimit-remaining": str(900 - thread_id),
                "x-ratelimit-limit": "1000",
            }
            state.update_from_headers(headers)
            return state.tokens_remaining

        # Run concurrent header updates
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(update_headers, i) for i in range(10)]
            results = [f.result() for f in futures]

        # Final state should be consistent (last update wins)
        state = limiter.get_state("race_token")
        assert state.tokens_remaining is not None
        assert state.tokens_remaining in results


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_rate_limit(self) -> None:
        """Test behavior with zero rate limit"""
        config = RateLimitConfig(max_requests_per_hour=0)
        limiter = BitbucketRateLimiter(config)

        state = limiter.get_state("zero_token")
        can_proceed, wait_time = state.can_make_request()

        # Should not be able to make any requests
        assert can_proceed is False
        assert wait_time is not None

    def test_very_high_rate_limit(self) -> None:
        """Test with very high rate limit"""
        config = RateLimitConfig(max_requests_per_hour=1000000, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)

        state = limiter.get_state("unlimited_token")

        # Should be able to make many requests
        for _ in range(1000):
            can_proceed, _ = state.can_make_request()
            assert can_proceed is True
            state.record_request()

    def test_retry_after_header_with_large_value(self) -> None:
        """Test Retry-After header with large value"""
        config = RateLimitConfig(
            respect_retry_after=True,
            max_delay=60.0,
            min_request_interval=0,
            max_retries=1,
        )
        limiter = BitbucketRateLimiter(config)

        # Create proper exception with large Retry-After
        class RateLimitError(Exception):
            def __init__(self) -> None:
                self.response = Mock()
                self.response.status_code = 429
                self.response.headers = {"Retry-After": "3600"}  # 1 hour

        # This should respect the retry-after even though it's > max_delay
        with patch("time.sleep") as mock_sleep:

            def mock_func() -> Never:
                raise RateLimitError()

            with contextlib.suppress(
                Exception
            ):  # Will raise RateLimitException after max_retries
                limiter.execute_with_retry(mock_func, key="retry_test")

            # Should have slept for retry-after value
            mock_sleep.assert_called_once_with(3600.0)

    def test_state_cleanup(self) -> None:
        """Test that old request times are cleaned up"""
        config = RateLimitConfig(max_requests_per_hour=10, min_request_interval=0)
        limiter = BitbucketRateLimiter(config)
        state = limiter.get_state("cleanup_token")

        # Add old requests (simulate requests from > 1 hour ago)
        old_time = time.time() - 3700  # 1 hour and 100 seconds ago
        with state.lock:
            for _ in range(5):
                state.request_times.append(old_time)

        # Add recent requests
        for _ in range(5):
            state.record_request()

        # Check state - old requests should be cleaned up
        can_proceed, _ = state.can_make_request()
        assert can_proceed is True  # Should be able to proceed (only 5 recent requests)

        # Request times should only contain recent requests
        assert len(state.request_times) == 5
