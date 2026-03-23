"""Credit tracking for YouTube API quota usage.

CreditCounter wraps a Redis INCRBY counter so that credit additions are
atomic even if multiple tasks share the same key.  The orchestrator
initialises the key at run-start from the persisted daily_usage value;
process_term and the YouTube helpers add to it throughout the run.
"""

import logging

import redis as redis_lib

logger = logging.getLogger(__name__)


class CreditLimitExceededError(Exception):
    """Raised when the YouTube daily credit quota is exhausted mid-run."""


# Backward-compatible alias
CreditLimitExceeded = CreditLimitExceededError


class CreditCounter:
    """Thread-safe, Redis-backed credit counter."""

    def __init__(
        self,
        redis_client: redis_lib.Redis,
        redis_key: str,
        initial: int | None = None,
    ) -> None:
        self._client = redis_client
        self._key = redis_key
        if initial is not None:
            self._client.set(self._key, initial)

    def add(self, n: int) -> int:
        """Atomically add n credits. Returns the new total."""
        return int(self._client.incrby(self._key, n))

    def total(self) -> int:
        """Return the current credit total."""
        val = self._client.get(self._key)
        return int(val) if val else 0

    def over_limit(self, limit: int) -> bool:
        """Return True if the current total is at or above limit."""
        return self.total() >= limit

    def add_and_raise_if_over(self, n: int, limit: int) -> int:
        """Add n credits, then raise CreditLimitExceededError if the limit is reached."""
        total = self.add(n)
        if total >= limit:
            raise CreditLimitExceededError(
                f"Daily credit limit of {limit} reached (used {total})"
            )
        return total

    def cleanup(self) -> None:
        """Remove the Redis key (call after run completes)."""
        self._client.delete(self._key)
