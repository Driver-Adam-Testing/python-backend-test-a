import time
from unittest.mock import Mock

import pytest
from pytest import MonkeyPatch

from .decorators import expiring_cache


@pytest.fixture
def mock_time(monkeypatch: MonkeyPatch) -> list[float]:
    """Fixture to mock `time.time` during tests."""
    current_time: list[float] = [time.time()]  # Use a mutable list to allow updates

    def mock_time_func() -> float:
        return current_time[0]

    monkeypatch.setattr(time, "time", mock_time_func)
    return current_time


def test_expiring_cache_caching(mock_time: list[float]) -> None:
    """Test that the decorator caches the result within the expiration time."""
    mock_func = Mock(return_value="cached_result")

    @expiring_cache(10)
    def wrapped_func() -> str:
        return mock_func()

    # Call the function twice within expiration time
    result1: str = wrapped_func()
    result2: str = wrapped_func()

    # Assert the result is cached and function is only called once
    assert result1 == "cached_result"
    assert result2 == "cached_result"
    assert mock_func.call_count == 1


def test_expiring_cache_expiry(mock_time: list[float]) -> None:
    """Test that the cache expires after the specified duration."""
    mock_func = Mock(return_value="new_result")

    @expiring_cache(10)
    def wrapped_func() -> str:
        return mock_func()

    # Call the function the first time
    result1: str = wrapped_func()
    assert result1 == "new_result"
    assert mock_func.call_count == 1

    # Simulate time advancing beyond expiration duration
    mock_time[0] += 11
    result2: str = wrapped_func()

    # Assert the function is called again and cache is refreshed
    assert result2 == "new_result"
    assert mock_func.call_count == 2


def test_expiring_cache_clear(mock_time: list[float]) -> None:
    """Test that clearing the cache forces a function call."""
    mock_func = Mock(return_value="cleared_result")

    @expiring_cache(10)
    def wrapped_func() -> str:
        return mock_func()

    # Call the function once
    result1: str = wrapped_func()
    assert result1 == "cleared_result"
    assert mock_func.call_count == 1

    # Clear the cache
    wrapped_func.clear_cache()

    # Call the function again
    result2: str = wrapped_func()
    assert result2 == "cleared_result"
    assert mock_func.call_count == 2
