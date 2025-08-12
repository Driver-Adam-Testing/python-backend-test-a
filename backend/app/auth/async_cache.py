import asyncio
import time
from typing import Any


class AsyncTTLCache:
    """Simple async TTL cache with size limit and LRU eviction."""

    def __init__(self, ttl: int = 600, max_size: int = 1000) -> None:
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
        self.ttl = ttl
        self.max_size = max_size

    async def get(self, key: str) -> Any | None:  # noqa: ANN401
        """Get value from cache if not expired."""
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    return value
                else:
                    # Clean up expired entry
                    del self._cache[key]
            return None

    async def set(self, key: str, value: Any) -> None:  # noqa: ANN401
        """Set value in cache with TTL."""
        async with self._lock:
            # Simple LRU: remove oldest entry if at capacity
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]

            self._cache[key] = (value, time.time() + self.ttl)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
