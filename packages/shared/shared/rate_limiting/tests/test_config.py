"""Unit tests for rate limiting configuration"""

import os
from unittest.mock import patch

import pytest

from shared.rate_limiting import RateLimitStrategy
from shared.rate_limiting.config import (
    get_bitbucket_rate_limit_config,
    get_rate_limit_config_for_provider,
)


class TestBitbucketRateLimitConfig:
    """Test Bitbucket rate limit configuration loading"""

    def test_default_config(self):
        """Test default configuration when no env vars are set"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_bitbucket_rate_limit_config()

            assert config.max_requests_per_hour == 1000
            assert config.max_retries == 5
            assert config.initial_delay == 1.0
            assert config.max_delay == 60.0
            assert config.backoff_factor == 2.0
            assert config.strategy == RateLimitStrategy.EXPONENTIAL_BACKOFF
            assert config.respect_retry_after is True
            assert config.min_request_interval == 0.1

    def test_env_var_override(self):
        """Test configuration override via environment variables"""
        env_vars = {
            "BITBUCKET_RATE_LIMIT_PER_HOUR": "500",
            "BITBUCKET_RATE_LIMIT_MAX_RETRIES": "3",
            "BITBUCKET_RATE_LIMIT_INITIAL_DELAY": "2.0",
            "BITBUCKET_RATE_LIMIT_MAX_DELAY": "30.0",
            "BITBUCKET_RATE_LIMIT_BACKOFF_FACTOR": "1.5",
            "BITBUCKET_RATE_LIMIT_STRATEGY": "fixed_delay",
            "BITBUCKET_RATE_LIMIT_RESPECT_RETRY_AFTER": "false",
            "BITBUCKET_RATE_LIMIT_MIN_INTERVAL": "0.5",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_bitbucket_rate_limit_config()

            assert config.max_requests_per_hour == 500
            assert config.max_retries == 3
            assert config.initial_delay == 2.0
            assert config.max_delay == 30.0
            assert config.backoff_factor == 1.5
            assert config.strategy == RateLimitStrategy.FIXED_DELAY
            assert config.respect_retry_after is False
            assert config.min_request_interval == 0.5

    def test_invalid_strategy_fallback(self):
        """Test fallback to default strategy for invalid value"""
        env_vars = {
            "BITBUCKET_RATE_LIMIT_STRATEGY": "invalid_strategy",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_bitbucket_rate_limit_config()

            # Should fallback to exponential backoff
            assert config.strategy == RateLimitStrategy.EXPONENTIAL_BACKOFF

    def test_token_bucket_strategy(self):
        """Test token bucket strategy configuration"""
        env_vars = {
            "BITBUCKET_RATE_LIMIT_STRATEGY": "token_bucket",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_bitbucket_rate_limit_config()

            assert config.strategy == RateLimitStrategy.TOKEN_BUCKET

    def test_partial_env_override(self):
        """Test that only specified env vars override defaults"""
        env_vars = {
            "BITBUCKET_RATE_LIMIT_PER_HOUR": "2000",
            "BITBUCKET_RATE_LIMIT_MIN_INTERVAL": "0.2",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_bitbucket_rate_limit_config()

            # Overridden values
            assert config.max_requests_per_hour == 2000
            assert config.min_request_interval == 0.2

            # Default values
            assert config.max_retries == 5
            assert config.initial_delay == 1.0
            assert config.strategy == RateLimitStrategy.EXPONENTIAL_BACKOFF


class TestProviderConfig:
    """Test provider-specific configurations"""

    def test_bitbucket_provider_config(self):
        """Test getting Bitbucket config via provider method"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_rate_limit_config_for_provider("bitbucket")

            assert config is not None
            assert config.max_requests_per_hour == 1000

    def test_github_provider_config(self):
        """Test GitHub provider configuration"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_rate_limit_config_for_provider("github")

            assert config is not None
            assert config.max_requests_per_hour == 5000  # GitHub default
            assert config.max_retries == 3
            assert config.min_request_interval == 0.05

    def test_github_env_override(self):
        """Test GitHub configuration with env vars"""
        env_vars = {
            "GITHUB_RATE_LIMIT_PER_HOUR": "10000",
            "GITHUB_RATE_LIMIT_MAX_RETRIES": "5",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_rate_limit_config_for_provider("github")

            assert config.max_requests_per_hour == 10000
            assert config.max_retries == 5

    def test_gitlab_provider_config(self):
        """Test GitLab provider configuration"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_rate_limit_config_for_provider("gitlab")

            assert config is not None
            assert config.max_requests_per_hour == 2000  # GitLab default
            assert config.max_retries == 3
            assert config.min_request_interval == 0.1

    def test_gitlab_env_override(self):
        """Test GitLab configuration with env vars"""
        env_vars = {
            "GITLAB_RATE_LIMIT_PER_HOUR": "3000",
            "GITLAB_RATE_LIMIT_MIN_INTERVAL": "0.2",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_rate_limit_config_for_provider("gitlab")

            assert config.max_requests_per_hour == 3000
            assert config.min_request_interval == 0.2

    def test_unsupported_provider(self):
        """Test unsupported provider returns None"""
        config = get_rate_limit_config_for_provider("unsupported")
        assert config is None

    def test_provider_case_insensitive(self):
        """Test provider name is case insensitive"""
        config1 = get_rate_limit_config_for_provider("BITBUCKET")
        config2 = get_rate_limit_config_for_provider("BitBucket")
        config3 = get_rate_limit_config_for_provider("bitbucket")

        assert config1 is not None
        assert config2 is not None
        assert config3 is not None

        # All should have same defaults
        assert config1.max_requests_per_hour == 1000
        assert config2.max_requests_per_hour == 1000
        assert config3.max_requests_per_hour == 1000

    def test_provider_specific_env_isolation(self):
        """Test that provider env vars don't affect each other"""
        env_vars = {
            "BITBUCKET_RATE_LIMIT_PER_HOUR": "1000",
            "GITHUB_RATE_LIMIT_PER_HOUR": "5000",
            "GITLAB_RATE_LIMIT_PER_HOUR": "2000",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            bitbucket_config = get_rate_limit_config_for_provider("bitbucket")
            github_config = get_rate_limit_config_for_provider("github")
            gitlab_config = get_rate_limit_config_for_provider("gitlab")

            assert bitbucket_config.max_requests_per_hour == 1000
            assert github_config.max_requests_per_hour == 5000
            assert gitlab_config.max_requests_per_hour == 2000


class TestConfigValidation:
    """Test configuration validation and edge cases"""

    def test_negative_values_handling(self):
        """Test handling of negative values in env vars"""
        env_vars = {
            "BITBUCKET_RATE_LIMIT_PER_HOUR": "-100",  # Negative value
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Pydantic accepts negative values - this is actually valid
            # The function doesn't validate the value, just parses it
            config = get_bitbucket_rate_limit_config()
            assert config.max_requests_per_hour == -100

    def test_non_numeric_values_handling(self):
        """Test handling of non-numeric values in numeric env vars"""
        env_vars = {
            "BITBUCKET_RATE_LIMIT_PER_HOUR": "abc",  # Invalid
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                config = get_bitbucket_rate_limit_config()

    def test_boolean_parsing(self):
        """Test boolean parsing for respect_retry_after"""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("yes", False),  # Not 'true', so False
            ("1", False),  # Not 'true', so False
            ("", False),  # Empty string, so False
        ]

        for value, expected in test_cases:
            env_vars = {
                "BITBUCKET_RATE_LIMIT_RESPECT_RETRY_AFTER": value,
            }

            with patch.dict(os.environ, env_vars, clear=True):
                config = get_bitbucket_rate_limit_config()
                assert (
                    config.respect_retry_after == expected
                ), f"Failed for value: {value}"

    def test_float_parsing(self):
        """Test float parsing for delay and interval values"""
        env_vars = {
            "BITBUCKET_RATE_LIMIT_INITIAL_DELAY": "1.5",
            "BITBUCKET_RATE_LIMIT_MAX_DELAY": "45.75",
            "BITBUCKET_RATE_LIMIT_BACKOFF_FACTOR": "2.25",
            "BITBUCKET_RATE_LIMIT_MIN_INTERVAL": "0.125",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_bitbucket_rate_limit_config()

            assert config.initial_delay == 1.5
            assert config.max_delay == 45.75
            assert config.backoff_factor == 2.25
            assert config.min_request_interval == 0.125
