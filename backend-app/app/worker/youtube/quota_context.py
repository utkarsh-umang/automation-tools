"""Multi-key YouTube API quota: per-key Redis counters and mid-term failover."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.worker.youtube.credits import CreditCounter, CreditLimitExceeded

if TYPE_CHECKING:
    import redis as redis_lib

logger = logging.getLogger(__name__)


class YouTubeQuotaContext:
    """Selects API key + counter per request; advances to next key when current is full."""

    def __init__(
        self,
        redis_client: redis_lib.Redis,
        date_iso: str,
        api_keys: list[str],
        per_key_limit: int,
        *,
        batch_id: str | None = None,
        term_id: str | None = None,
    ) -> None:
        self._redis = redis_client
        self._date = date_iso
        self._keys = api_keys
        self._limit = per_key_limit
        self._batch_id = batch_id
        self._term_id = term_id
        self._counters: list[CreditCounter] = [
            CreditCounter(redis_client, f"yt_credits:{date_iso}:k{i}")
            for i in range(len(api_keys))
        ]
        self._index = 0

    @property
    def per_key_limit(self) -> int:
        return self._limit

    def prepare_for_charge(self, cost: int) -> tuple[str, CreditCounter]:
        """Return ``(api_key, counter)`` for a request that will cost ``cost`` units.

        If the current key cannot fit ``cost`` without exceeding the per-key daily
        limit, advances to the next key. If the last key cannot fit the charge,
        raises :class:`CreditLimitExceeded`.
        """
        while True:
            counter = self._counters[self._index]
            if counter.total() + cost <= self._limit:
                return self._keys[self._index], counter
            if self._index < len(self._keys) - 1:
                old = self._index
                self._index += 1
                logger.info(
                    "youtube_key_failover batch_id=%s term_id=%s from_key_index=%s to_key_index=%s",
                    self._batch_id,
                    self._term_id,
                    old,
                    self._index,
                )
            else:
                raise CreditLimitExceeded(
                    f"Daily credit limit {self._limit} reached on last API key "
                    f"(index {self._index})"
                )

    def total_all(self) -> int:
        """Sum of credits used across all configured keys today."""
        return sum(c.total() for c in self._counters)

    def totals_by_key_index(self) -> dict[str, int]:
        return {str(i): c.total() for i, c in enumerate(self._counters)}

    def all_keys_exhausted(self) -> bool:
        """True when every key is at or above the per-key limit."""
        return all(c.over_limit(self._limit) for c in self._counters)


def seed_redis_from_mongo(
    redis_client: redis_lib.Redis,
    date_iso: str,
    num_keys: int,
    credits_by_key: dict[str, int],
) -> None:
    """Overwrite per-key Redis counters from persisted Mongo values (batch run start)."""
    for i in range(num_keys):
        rk = f"yt_credits:{date_iso}:k{i}"
        initial = int(credits_by_key.get(str(i), 0))
        CreditCounter(redis_client, rk, initial=initial)


def aggregate_from_redis(
    redis_client: redis_lib.Redis,
    date_iso: str,
    num_keys: int,
) -> tuple[int, dict[str, int]]:
    """Read per-key totals from Redis and return ``(sum, {index: total})``."""
    by_key: dict[str, int] = {}
    total = 0
    for i in range(num_keys):
        c = CreditCounter(redis_client, f"yt_credits:{date_iso}:k{i}")
        t = c.total()
        by_key[str(i)] = t
        total += t
    return total, by_key


def all_keys_exhausted(
    redis_client: redis_lib.Redis,
    date_iso: str,
    num_keys: int,
    per_key_limit: int,
) -> bool:
    """Whether every per-key Redis counter is at or above ``per_key_limit``."""
    for i in range(num_keys):
        c = CreditCounter(redis_client, f"yt_credits:{date_iso}:k{i}")
        if c.total() < per_key_limit:
            return False
    return True
