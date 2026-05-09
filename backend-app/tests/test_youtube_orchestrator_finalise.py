import pytest


def test_finalise_pauses_when_pending_terms_remain(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: never mark batch completed if pending/running terms exist."""
    from app.worker import orchestrator as orch

    calls: list[tuple] = []

    monkeypatch.setattr(
        orch.search_term_repo,
        "get_all_for_batch",
        lambda _bid: [{"status": "done"}, {"status": "pending"}],
    )
    monkeypatch.setattr(
        orch.batch_repo,
        "update_status",
        lambda batch_id, status, **kwargs: calls.append((batch_id, status.value, kwargs)),
    )
    monkeypatch.setattr(orch.daily_usage_repo, "clear_active_batch", lambda: None)
    monkeypatch.setattr(orch.daily_usage_repo, "increment_runs", lambda: None)
    monkeypatch.setattr(orch, "aggregate_from_redis", lambda *_args, **_kwargs: (0, {}))
    monkeypatch.setattr(orch.job_log_repo, "append", lambda *_args, **_kwargs: None)

    orch._finalise("b1", redis_client=None, today="2026-01-01", n_keys=1, credits_at_start=0)  # noqa: SLF001

    assert calls, "Expected batch_repo.update_status to be called"
    assert calls[0][1] == "paused"


def test_run_pauses_and_rolls_back_only_current_term_on_credit_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: credit limit hit should pause immediately, not mark later terms running."""
    from app.schemas.youtube.batch import BatchStatus
    from app.worker import orchestrator as orch
    from app.worker.youtube.credits import CreditLimitExceeded

    # --- stubs / recorders ---
    class _FakeRedis:  # minimal redis stub for seed/aggregate calls
        def set(self, *_args, **_kwargs):  # noqa: ANN001
            return True

        def delete(self, *_args, **_kwargs):  # noqa: ANN001
            return None

    updates: list[tuple[str, str]] = []
    reset_calls: list[str] = []
    process_calls: list[str] = []

    monkeypatch.setattr(orch, "get_ordered_youtube_api_keys", lambda: ["k1"])
    monkeypatch.setattr(orch.config, "YOUTUBE_DAILY_CREDIT_LIMIT", 100)
    monkeypatch.setattr(orch, "seed_redis_from_mongo", lambda *_a, **_k: None)
    monkeypatch.setattr(orch, "aggregate_from_redis", lambda *_a, **_k: (0, {}))
    monkeypatch.setattr(orch, "all_keys_exhausted", lambda *_a, **_k: False)

    monkeypatch.setattr(orch.batch_repo, "get_by_id", lambda _bid: {"_id": _bid, "status": BatchStatus.QUEUED.value})
    monkeypatch.setattr(
        orch.batch_repo,
        "update_status",
        lambda batch_id, status, **_kwargs: updates.append((batch_id, status.value)),
    )
    monkeypatch.setattr(orch.daily_usage_repo, "get_or_create_today", lambda: {"activeBatchId": None})
    monkeypatch.setattr(orch.daily_usage_repo, "set_active_batch", lambda *_a, **_k: None)
    monkeypatch.setattr(orch.daily_usage_repo, "clear_active_batch", lambda *_a, **_k: None)
    monkeypatch.setattr(orch.daily_usage_repo, "set_credits_used_and_by_key", lambda *_a, **_k: None)
    monkeypatch.setattr(orch.job_log_repo, "append", lambda *_a, **_k: None)

    monkeypatch.setattr(
        orch.search_term_repo,
        "get_pending_for_batch",
        lambda _bid: [{"_id": "t1", "term": "kw1"}, {"_id": "t2", "term": "kw2"}],
    )
    monkeypatch.setattr(
        orch.search_term_repo,
        "reset_to_pending",
        lambda term_id: reset_calls.append(term_id),
    )

    def _process_term(_batch_id: str, term_id: str, _today: str) -> None:
        process_calls.append(term_id)
        raise CreditLimitExceeded("quota")

    monkeypatch.setattr(orch, "process_term", _process_term)

    orch._run("b1", _FakeRedis())  # noqa: SLF001

    # Only first term should have been attempted; second remains pending.
    assert process_calls == ["t1"]
    # Current term rolled back to pending.
    assert reset_calls == ["t1"]
    # Batch should end paused.
    assert ("b1", "paused") in updates

