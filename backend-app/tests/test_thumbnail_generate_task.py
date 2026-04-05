"""Tests for ``generate_thumbnail_task`` (Celery thumbnail pipeline)."""

from __future__ import annotations

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded

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
                    with patch(
                        "ai_agents.run_thumbnail_agent",
                    ) as agent:
                        agent.return_value = {
                            "image_bytes": b"\x89PNG\r\n",
                            "prompt_used": "prompt text",
                        }
                        with patch.object(
                            gen_mod, "upload_thumbnail_png", return_value="https://s3/u"
                        ) as up:
                            with patch.object(
                                gen_mod.mongo_repo,
                                "update_prompt_used",
                            ) as mp:
                                with patch.object(
                                    gen_mod.pg_repo,
                                    "update_completed",
                                    new_callable=AsyncMock,
                                ) as uc:
                                    await gen_mod._async_generate_thumbnail(
                                        job_id, time.perf_counter()
                                    )

                                    us.assert_awaited_once()
                                    agent.assert_called_once()
                                    up.assert_called_once_with(
                                        job_id, b"\x89PNG\r\n"
                                    )
                                    mp.assert_called_once_with(
                                        job_id, "prompt text"
                                    )
                                    assert uc.await_args is not None
                                    assert uc.await_args.args[1] == uid
                                    assert uc.await_args.args[2] == "https://s3/u"


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
                    with patch(
                        "ai_agents.run_thumbnail_agent",
                    ) as agent:
                        agent.return_value = {"image_bytes": b"x", "prompt_used": "p"}
                        with patch.object(
                            gen_mod, "upload_thumbnail_png", return_value="u"
                        ):
                            with patch.object(
                                gen_mod.mongo_repo, "update_prompt_used"
                            ):
                                with patch.object(
                                    gen_mod.pg_repo,
                                    "update_completed",
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
