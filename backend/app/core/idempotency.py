import time
from typing import Dict, Any, Optional

class IdempotencyCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache: Dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached response if it exists and is not expired."""
        self._cleanup()
        if key in self.cache:
            timestamp, val = self.cache[key]
            if time.time() - timestamp <= self.ttl:
                return val
        return None

    def set(self, key: str, value: Any) -> None:
        """Cache the response with current timestamp."""
        self.cache[key] = (time.time(), value)
        self._cleanup()

    def clear(self) -> None:
        """Clear all cache contents (mainly for testing)."""
        self.cache.clear()

    def _cleanup(self) -> None:
        """Remove expired cache entries."""
        now = time.time()
        expired = [k for k, (t, _) in self.cache.items() if now - t > self.ttl]
        for k in expired:
            del self.cache[k]


_IDEMPOTENCY_CACHE = IdempotencyCache()


def get_idempotency_cache() -> IdempotencyCache:
    return _IDEMPOTENCY_CACHE
