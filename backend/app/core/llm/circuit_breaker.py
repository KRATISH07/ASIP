import time
import asyncio
from typing import Any, Optional
from app.core.logging import get_logger

logger = get_logger("llm_circuit_breaker")


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted but the circuit breaker is OPEN."""
    pass


class CircuitBreaker:
    """Thread-safe circuit breaker for LLM calls.

    All state-mutating methods are async and protected by asyncio.Lock to
    prevent race conditions when multiple concurrent requests call them
    simultaneously within the same event loop.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout_seconds: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds

        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.failure_count = 0
        self.last_state_change = time.time()
        # Lock guards all mutations to state and failure_count under async concurrency.
        self._lock = asyncio.Lock()

    async def record_success(self) -> None:
        """Record a successful execution, closing the breaker if it was HALF-OPEN."""
        async with self._lock:
            if self.state == "HALF-OPEN":
                logger.info("Circuit breaker closed: probe request succeeded")
                self.state = "CLOSED"
            self.failure_count = 0

    async def record_failure(self, error: Exception) -> None:
        """Record a failed execution. If threshold reached or HALF-OPEN, open the breaker."""
        async with self._lock:
            self.failure_count += 1
            logger.warning(
                "Circuit breaker failure recorded",
                state=self.state,
                failure_count=self.failure_count,
                error=type(error).__name__,
                detail=str(error)[:150],
            )
            if self.state == "HALF-OPEN" or (
                self.state == "CLOSED" and self.failure_count >= self.failure_threshold
            ):
                logger.error(
                    "Circuit breaker opened due to consecutive failures",
                    failure_count=self.failure_count,
                    trigger_error=type(error).__name__,
                )
                self.state = "OPEN"
                self.last_state_change = time.time()

    async def allow_request(self) -> bool:
        """Determine if a request should be allowed. Transitions OPEN -> HALF-OPEN if timeout expires."""
        async with self._lock:
            now = time.time()
            if self.state == "OPEN":
                if now - self.last_state_change > self.recovery_timeout:
                    logger.info("Circuit breaker half-opened: entering probe state after recovery timeout")
                    self.state = "HALF-OPEN"
                    self.last_state_change = now
                    return True
                return False
            return True

    def reset(self) -> None:
        """Reset circuit breaker to default CLOSED state (sync — for tests only)."""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_state_change = time.time()


_LLM_CIRCUIT_BREAKER = CircuitBreaker()


def get_circuit_breaker() -> CircuitBreaker:
    return _LLM_CIRCUIT_BREAKER
