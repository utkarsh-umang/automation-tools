"""Unit tests for batch finalization guards."""

import pytest
from fastapi import HTTPException

from app.controllers.youtube import batches as batches_module


def test_finalize_terms_must_all_be_done_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        batches_module.search_term_repo,
        "get_all_for_batch",
        lambda _bid: [{"status": "done"}, {"status": "done"}],
    )
    batches_module._finalize_terms_must_all_be_done("batch1")  # noqa: SLF001


def test_finalize_terms_must_all_be_done_raises_when_not_all_done(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        batches_module.search_term_repo,
        "get_all_for_batch",
        lambda _bid: [
            {"status": "done"},
            {"status": "failed"},
            {"status": "pending"},
        ],
    )
    with pytest.raises(HTTPException) as exc:
        batches_module._finalize_terms_must_all_be_done("batch1")  # noqa: SLF001
    assert exc.value.status_code == 400
    assert "failed" in exc.value.detail
    assert "pending" in exc.value.detail
