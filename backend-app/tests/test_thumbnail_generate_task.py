"""Tests for ``generate_thumbnail_task`` (Celery thumbnail pipeline)."""

from __future__ import annotations

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from celery.exceptions import MaxRetriesExceededError, Retry, SoftTimeLimitExceeded

from app.worker.thumbnail import generate as gen_mod
from app.worker.thumbnail.generate import generate_thumbnail_task


def _session_context_mocks() -> tuple[MagicMock, AsyncMock]:
    session = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm, session


@pytest.mark.asyncio
async def test_async_skips_when_already_completed() -> None:
    job_id = str(uuid.uuid4())
    sess_cm, _ = _session_context_mocks()
    with patch("app.worker.thumbnail.generate.AsyncSessionLocal", return_value=sess_cm):
        with patch.object(
            gen_mod.pg_repo,
            "get_job",
            new_callable=AsyncMock,
            return_value={"status": "completed", "result_url": "https://cdn/x.png"},
        ):
            with patch.object(
                gen_mod.pg_repo, "update_status", new_callable=AsyncMock
            ) as us:
                await gen_mod._async_generate_thumbnail(job_id, time.perf_counter())
                us.assert_not_awaited()


@pytest.mark.asyncio
async def test_async_success_pipeline_order() -> None:
    job_id = str(uuid.uuid4())
    uid = uuid.UUID(job_id)
    sess_cm, session = _session_context_mocks()

    with patch("app.worker.thumbnail.generate.AsyncSessionLocal", return_value=sess_cm):
        with patch.object(
            gen_mod.pg_repo,
            "get_job",
            new_callable=AsyncMock,
            return_value={"status": "pending", "result_url": None},
        ):
            with patch.object(
                gen_mod.pg_repo, "update_status", new_callable=AsyncMock
            ) as us:
                with patch.object(
                    gen_mod.mongo_repo,
                    "get_details",
                    return_value={
                        "reference_image_url": "https://ex/ref.jpg",
                        "base_image_urls": ["https://ex/b.jpg"],
                        "title": "T",
                        "include_title": True,
                        "creative_comments": "c",
                        "model": "gptimage",
                    },
                ):
                    with patch.object(
                        gen_mod, "run_thumbnail_agent"
                    ) as agent:
                        agent.return_value = {
                            "images": [b"\x89PNG\r\n", b"\x89PNG\r\n2"],
                            "prompt_used": "prompt text",
                        }
                        with patch.object(
                            gen_mod,
                            "upload_thumbnail_png_candidate",
                            side_effect=lambda jid, i, img: f"https://s3/u{i}",
                        ) as up:
                            with patch.object(
                                gen_mod.mongo_repo,
                                "update_prompt_used",
                            ) as mp:
                                with patch.object(
                                    gen_mod.pg_repo,
                                    "update_candidates",
                                    new_callable=AsyncMock,
                                ) as uc:
                                    await gen_mod._async_generate_thumbnail(
                                        job_id, time.perf_counter()
                                    )

                                    us.assert_awaited_once()
                                    agent.assert_called_once()
                                    assert agent.call_args[1]["num_candidates"] == 2
                                    assert up.call_count == 2
                                    up.assert_any_call(job_id, 0, b"\x89PNG\r\n")
                                    up.assert_any_call(job_id, 1, b"\x89PNG\r\n2")
                                    mp.assert_called_once_with(
                                        job_id, "prompt text"
                                    )
                                    assert uc.await_args is not None
                                    assert uc.await_args.args[1] == uid
                                    assert uc.await_args.args[2] == [
                                        "https://s3/u0",
                                        "https://s3/u1",
                                    ]


@pytest.mark.asyncio
async def test_async_uses_s3_keys_for_agent_urls() -> None:
    job_id = str(uuid.uuid4())
    sess_cm, _ = _session_context_mocks()
    ref_key = f"thumbnail-inputs/{job_id}/reference.png"
    base_keys = [f"thumbnail-inputs/{job_id}/base/0.jpg"]

    with patch("app.worker.thumbnail.generate.AsyncSessionLocal", return_value=sess_cm):
        with patch.object(
            gen_mod.pg_repo,
            "get_job",
            new_callable=AsyncMock,
            return_value={"status": "pending", "result_url": None},
        ):
            with patch.object(gen_mod.pg_repo, "update_status", new_callable=AsyncMock):
                with patch.object(
                    gen_mod.mongo_repo,
                    "get_details",
                    return_value={
                        "reference_image_url": "https://stale.invalid/old",
                        "base_image_urls": ["https://stale.invalid/old-base"],
                        "reference_image_s3_key": ref_key,
                        "base_image_s3_keys": base_keys,
                        "title": "T",
                        "include_title": True,
                        "creative_comments": "c",
                        "model": "gptimage",
                    },
                ):
                    with patch.object(
                        gen_mod, "run_thumbnail_agent"
                    ) as agent:
                        agent.return_value = {
                            "images": [b"\x89PNG\r\n", b"\x89PNG\r\n2"],
                            "prompt_used": None,
                        }
                        with patch.object(
                            gen_mod,
                            "get_s3_object_read_url",
                            side_effect=lambda k: f"resolved:{k}",
                        ) as gsu:
                            with patch.object(
                                gen_mod,
                                "upload_thumbnail_png_candidate",
                                side_effect=lambda jid, i, img: "https://s3/u",
                            ):
                                with patch.object(
                                    gen_mod.mongo_repo, "update_prompt_used"
                                ) as mp:
                                    with patch.object(
                                        gen_mod.pg_repo,
                                        "update_candidates",
                                        new_callable=AsyncMock,
                                    ):
                                        await gen_mod._async_generate_thumbnail(
                                            job_id, time.perf_counter()
                                        )
                                        mp.assert_not_called()
                                        gsu.assert_any_call(ref_key)
                                        gsu.assert_any_call(base_keys[0])
                                        agent.assert_called_once()
                                        kw = agent.call_args[1]
                                        assert kw["reference_image_url"] == f"resolved:{ref_key}"
                                        assert kw["base_image_urls"] == [
                                            f"resolved:{base_keys[0]}"
                                        ]


@pytest.mark.asyncio
async def test_async_calls_nanobanana_model() -> None:
    job_id = str(uuid.uuid4())
    sess_cm, _ = _session_context_mocks()
    with patch("app.worker.thumbnail.generate.AsyncSessionLocal", return_value=sess_cm):
        with patch.object(
            gen_mod.pg_repo,
            "get_job",
            new_callable=AsyncMock,
            return_value={"status": "pending", "result_url": None},
        ):
            with patch.object(gen_mod.pg_repo, "update_status", new_callable=AsyncMock):
                with patch.object(
                    gen_mod.mongo_repo,
                    "get_details",
                    return_value={
                        "reference_image_url": "r",
                        "base_image_urls": ["b"],
                        "title": "t",
                        "include_title": False,
                        "creative_comments": "",
                        "model": "nanobanana",
                    },
                ):
                    with patch.object(
                        gen_mod, "run_thumbnail_agent"
                    ) as agent:
                        agent.return_value = {"images": [b"x", b"y"], "prompt_used": "p"}
                        with patch.object(
                            gen_mod,
                            "upload_thumbnail_png_candidate",
                            side_effect=lambda jid, i, img: "u",
                        ):
                            with patch.object(
                                gen_mod.mongo_repo, "update_prompt_used"
                            ):
                                with patch.object(
                                    gen_mod.pg_repo,
                                    "update_candidates",
                                    new_callable=AsyncMock,
                                ):
                                    await gen_mod._async_generate_thumbnail(
                                        job_id, time.perf_counter()
                                    )
                                    agent.assert_called_once()
                                    call_kw = agent.call_args[1]
                                    assert call_kw["model"] == "nanobanana"


def test_soft_timeout_marks_failed() -> None:
    jid = str(uuid.uuid4())

    def _close_coro_and_raise_soft_limit(coro):  # type: ignore[no-untyped-def]
        coro.close()
        raise SoftTimeLimitExceeded()

    with patch(
        "app.worker.thumbnail.generate.asyncio.run",
        side_effect=_close_coro_and_raise_soft_limit,
    ):
        with patch(
            "app.worker.thumbnail.generate._run_mark_pg_failed"
        ) as mf:
            with pytest.raises(SoftTimeLimitExceeded):
                generate_thumbnail_task.run(jid)
            mf.assert_called_once_with(jid, gen_mod._TIMEOUT_USER_MESSAGE)


def test_max_retries_marks_failed_with_truncation() -> None:
    jid = str(uuid.uuid4())
    long_msg = "x" * 600

    def _close_coro_and_raise_value(coro):  # type: ignore[no-untyped-def]
        coro.close()
        raise ValueError(long_msg)

    with patch(
        "app.worker.thumbnail.generate.asyncio.run",
        side_effect=_close_coro_and_raise_value,
    ):
        with patch.object(
            generate_thumbnail_task,
            "retry",
            side_effect=MaxRetriesExceededError(),
        ):
            with patch(
                "app.worker.thumbnail.generate._run_mark_pg_failed"
            ) as mf:
                with patch(
                    "app.worker.thumbnail.generate.capture_thumbnail_task_exhausted_retries"
                ) as cap:
                    generate_thumbnail_task.run(jid)
                mf.assert_called_once()
                _jid, msg = mf.call_args[0]
                assert _jid == jid
                assert len(msg) == 500
                cap.assert_called_once()


def test_scheduled_retry_does_not_mark_failed() -> None:
    """A normal, successfully-scheduled retry (Retry raised, retries remain)
    must propagate to Celery untouched — not be treated as exhausted."""
    jid = str(uuid.uuid4())

    def _close_coro_and_raise_value(coro):  # type: ignore[no-untyped-def]
        coro.close()
        raise ValueError("transient error")

    with patch(
        "app.worker.thumbnail.generate.asyncio.run",
        side_effect=_close_coro_and_raise_value,
    ):
        with patch.object(
            generate_thumbnail_task,
            "retry",
            side_effect=Retry("retry scheduled"),
        ):
            with patch(
                "app.worker.thumbnail.generate._run_mark_pg_failed"
            ) as mf:
                with pytest.raises(Retry):
                    generate_thumbnail_task.run(jid)
                mf.assert_not_called()


def test_retry_reraising_original_exception_still_marks_failed() -> None:
    """Regression: some Celery configs re-raise the original exception directly
    on exhausted retries instead of MaxRetriesExceededError (seen in production —
    a ValueError propagated as "raised unexpected" and left the job stuck at its
    last-known status instead of being marked failed). Any non-Retry exception
    out of self.retry() must still mark the job failed.
    """
    jid = str(uuid.uuid4())

    def _close_coro_and_raise_value(coro):  # type: ignore[no-untyped-def]
        coro.close()
        raise ValueError("Unsupported thumbnail model: 'fluxkontext'")

    with patch(
        "app.worker.thumbnail.generate.asyncio.run",
        side_effect=_close_coro_and_raise_value,
    ):
        with patch.object(
            generate_thumbnail_task,
            "retry",
            side_effect=ValueError("Unsupported thumbnail model: 'fluxkontext'"),
        ):
            with patch(
                "app.worker.thumbnail.generate._run_mark_pg_failed"
            ) as mf:
                with patch(
                    "app.worker.thumbnail.generate.capture_thumbnail_task_exhausted_retries"
                ) as cap:
                    generate_thumbnail_task.run(jid)
                mf.assert_called_once_with(
                    jid, "Unsupported thumbnail model: 'fluxkontext'"
                )
                cap.assert_called_once()
