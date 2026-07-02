"""Watchdog: scheduler reaps a batch orphaned by a dead worker.

Guards the P0 where a worker crash mid-run left activeBatchId set and deadlocked
the auto-trigger queue until the Pacific-midnight rollover.
"""

import pytest


class _FakeRedis:
    def __init__(self, keys: dict[str, object]) -> None:
        self._keys = keys

    def get(self, key: str):  # noqa: ANN201
        return self._keys.get(key)


def _wire(monkeypatch, *, usage, lock_present, batch):
    """Stub scheduler deps; return a dict recording side effects."""
    from app.worker import scheduler as sched

    rec: dict[str, object] = {"status_updates": [], "cleared": False, "logs": []}

    monkeypatch.setattr(sched.daily_usage_repo, "get_today", lambda: usage)
    lock_key = f"batch_lock:{(usage or {}).get('activeBatchId')}"
    monkeypatch.setattr(
        sched, "get_raw_redis", lambda: _FakeRedis({lock_key: "1"} if lock_present else {})
    )
    monkeypatch.setattr(sched.batch_repo, "get_by_id", lambda _bid: batch)
    monkeypatch.setattr(
        sched.batch_repo,
        "update_status",
        lambda bid, status, **kw: rec["status_updates"].append((bid, status.value)),
    )
    monkeypatch.setattr(
        sched.job_log_repo, "append", lambda *a, **k: rec["logs"].append(a)
    )

    def _clear() -> None:
        rec["cleared"] = True

    monkeypatch.setattr(sched.daily_usage_repo, "clear_active_batch", _clear)
    return sched, rec


def test_no_active_batch_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    sched, rec = _wire(monkeypatch, usage={"activeBatchId": None}, lock_present=False, batch=None)
    sched._reap_stale_active_batch()  # noqa: SLF001
    assert rec["status_updates"] == []
    assert rec["cleared"] is False


def test_live_lock_is_not_reaped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A running batch (lock alive) must be left alone."""
    sched, rec = _wire(
        monkeypatch,
        usage={"activeBatchId": "b1"},
        lock_present=True,
        batch={"_id": "b1", "status": "running"},
    )
    sched._reap_stale_active_batch()  # noqa: SLF001
    assert rec["status_updates"] == []
    assert rec["cleared"] is False


def test_orphaned_running_batch_is_reaped(monkeypatch: pytest.MonkeyPatch) -> None:
    """activeBatchId set + no lock + RUNNING → reset to PAUSED and clear the flag."""
    sched, rec = _wire(
        monkeypatch,
        usage={"activeBatchId": "b1"},
        lock_present=False,
        batch={"_id": "b1", "status": "running"},
    )
    sched._reap_stale_active_batch()  # noqa: SLF001
    assert ("b1", "paused") in rec["status_updates"]
    assert rec["cleared"] is True
