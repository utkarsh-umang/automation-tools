"""Tests for multi-key YouTube quota failover."""

import pytest

from app.worker.youtube.credits import CreditLimitExceeded
from app.worker.youtube.quota_context import YouTubeQuotaContext


class _FakeRedis:
    """Minimal Redis stub (decode_responses=True behaviour)."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str | int) -> None:
        self._data[key] = str(value)

    def incrby(self, key: str, n: int) -> int:
        cur = int(self._data.get(key, "0"))
        nxt = cur + n
        self._data[key] = str(nxt)
        return nxt


def test_prepare_for_charge_advances_when_first_key_full() -> None:
    r = _FakeRedis()
    r.set("yt_credits:2026-01-01:k0", "10000")
    r.set("yt_credits:2026-01-01:k1", "0")
    q = YouTubeQuotaContext(
        r,
        "2026-01-01",
        ["k-a", "k-b"],
        10000,
        batch_id="b1",
        term_id="t1",
    )
    api_key, counter = q.prepare_for_charge(100)
    assert api_key == "k-b"
    assert counter.total() == 0


def test_prepare_for_charge_raises_on_last_key() -> None:
    r = _FakeRedis()
    r.set("yt_credits:2026-01-01:k0", "10000")
    q = YouTubeQuotaContext(r, "2026-01-01", ["only"], 10000)
    with pytest.raises(CreditLimitExceeded):
        q.prepare_for_charge(1)


def test_total_all_sums_keys() -> None:
    r = _FakeRedis()
    r.set("yt_credits:2026-01-01:k0", "100")
    r.set("yt_credits:2026-01-01:k1", "200")
    q = YouTubeQuotaContext(r, "2026-01-01", ["a", "b"], 10000)
    assert q.total_all() == 300
