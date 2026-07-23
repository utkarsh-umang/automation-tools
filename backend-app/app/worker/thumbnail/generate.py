"""Celery task: generate thumbnail candidates via ``ai_agents``, upload to S3, persist state.

Flow (SBL-13): Mongo details → PG ``processing`` → ``run_thumbnail_agent``
(``num_candidates=2``, generated concurrently) → S3 (one object per candidate)
→ Mongo ``prompt_used`` → PG ``awaiting_selection`` with ``candidate_urls`` set.
The caller picks one via ``thumbnail_service.select_thumbnail_candidate``, which
moves the job to ``completed``. Idempotent if already ``completed`` with
``result_url``, or already ``awaiting_selection`` with candidates set (SBL-13).

Retries (SBL-14): ``max_retries=1``, ``countdown=10``; final failure stores up to
500 chars in PG ``error``. Time limits (SBL-16): soft 300s / hard 360s (image
renders legitimately take ~90-100s each); soft timeout marks PG failed with a
fixed message.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from celery.exceptions import Retry, SoftTimeLimitExceeded

from app.celery_app import celery_app
from app.core.error_reporting import capture_thumbnail_task_exhausted_retries
from app.db.session import AsyncSessionLocal, engine
from app.repositories import mongo_repo, pg_repo
from app.services.s3_upload import get_s3_object_read_url
from app.services.thumbnail_s3 import upload_thumbnail_png_candidate

from ai_agents import run_thumbnail_agent

logger = logging.getLogger(__name__)

_MAX_PG_ERROR_LEN = 500
_TIMEOUT_USER_MESSAGE = "Task timed out after 300s"
_NUM_CANDIDATES = 2


def _truncate_error_message(exc: BaseException) -> str:
    return str(exc)[:_MAX_PG_ERROR_LEN]


async def _mark_pg_failed(job_id: uuid.UUID, message: str) -> None:
    clipped = message[:_MAX_PG_ERROR_LEN]
    async with AsyncSessionLocal() as session:
        await pg_repo.update_failed(session, job_id, clipped)
        await session.commit()


def _run_mark_pg_failed(job_id_str: str, message: str) -> None:
    _run_async_pg(_mark_pg_failed(uuid.UUID(job_id_str), message))


def _failure_log_message(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {_truncate_error_message(exc)}"


def _run_async_pg(coro):
    """Run async DB work; dispose the engine so pools are not reused across event loops.

    Each Celery task uses ``asyncio.run``, which creates a new loop. asyncpg
    connections are bound to the loop that created them; reusing the global
    engine pool across loops triggers "another operation is in progress".
    """

    async def _runner():
        try:
            return await coro
        finally:
            await engine.dispose(close=True)

    return asyncio.run(_runner())


async def _async_generate_thumbnail(job_id: str, t0: float) -> None:
    uid = uuid.UUID(job_id)

    async with AsyncSessionLocal() as session:
        job = await pg_repo.get_job(session, uid)
        if job is None:
            raise ValueError(f"Thumbnail job not found: {job_id}")
        if job.get("status") == "completed" and job.get("result_url"):
            logger.info(
                "thumbnail.generate event=skip_idempotent job_id=%s",
                job_id,
            )
            return
        if job.get("status") == "awaiting_selection" and job.get("candidate_urls"):
            logger.info(
                "thumbnail.generate event=skip_idempotent_awaiting_selection job_id=%s",
                job_id,
            )
            return

    details = mongo_repo.get_details(job_id)
    if not details:
        raise ValueError(f"Thumbnail job details missing in Mongo: {job_id}")

    ref_key = details.get("reference_image_s3_key")
    if ref_key:
        reference_image_url = get_s3_object_read_url(str(ref_key))
    else:
        reference_image_url = details["reference_image_url"]

    base_keys_raw = details.get("base_image_s3_keys")
    if base_keys_raw is not None:
        base_image_urls = [get_s3_object_read_url(str(k)) for k in base_keys_raw]
    else:
        base_image_urls = list(details.get("base_image_urls") or [])

    model = details.get("model")
    if model not in ("gptimage", "nanobanana", "fluxkontext"):
        raise ValueError(f"Unsupported thumbnail model: {model!r}")

    logger.info(
        "thumbnail.generate event=task_started job_id=%s model=%s",
        job_id,
        model,
    )

    async with AsyncSessionLocal() as session:
        await pg_repo.update_status(session, uid, "processing")
        await session.commit()

    logger.info(
        "thumbnail.generate event=marked_processing job_id=%s model=%s",
        job_id,
        model,
    )

    t_agent = time.perf_counter()
    result = run_thumbnail_agent(
        model=model,
        reference_image_url=reference_image_url,
        base_image_urls=base_image_urls,
        title=details["title"],
        include_title=bool(details["include_title"]),
        creative_comments=details["creative_comments"],
        shorts_or_reels=bool(details.get("shorts_or_reels", False)),
        num_candidates=_NUM_CANDIDATES,
    )
    agent_ms = int((time.perf_counter() - t_agent) * 1000)
    logger.info(
        "thumbnail.generate event=agent_call_completed job_id=%s model=%s "
        "duration_ms=%s",
        job_id,
        model,
        agent_ms,
    )

    raw_images = result.get("images")
    if not isinstance(raw_images, list) or not raw_images:
        raise TypeError("run_thumbnail_agent did not return a non-empty images list")
    images = [bytes(img) for img in raw_images]
    prompt_used = result.get("prompt_used")
    prompt_str = None if prompt_used is None else str(prompt_used)

    t_s3 = time.perf_counter()
    candidate_urls = [
        upload_thumbnail_png_candidate(job_id, i, img) for i, img in enumerate(images)
    ]
    s3_ms = int((time.perf_counter() - t_s3) * 1000)
    logger.info(
        "thumbnail.generate event=s3_upload_completed job_id=%s model=%s "
        "candidates=%s duration_ms=%s",
        job_id,
        model,
        len(candidate_urls),
        s3_ms,
    )

    if prompt_str is not None:
        mongo_repo.update_prompt_used(job_id, prompt_str)

    async with AsyncSessionLocal() as session:
        await pg_repo.update_candidates(session, uid, candidate_urls)
        await session.commit()

    total_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(
        "thumbnail.generate event=task_completed job_id=%s model=%s "
        "candidates=%s total_duration_ms=%s",
        job_id,
        model,
        len(candidate_urls),
        total_ms,
    )


@celery_app.task(
    bind=True,
    name="thumbnail.generate_thumbnail",
    max_retries=1,
    # gpt-image-2 / Gemini renders legitimately take ~90-100s each; two
    # candidates generate concurrently, so wall-clock is ~one render plus
    # contention. The image-model clients themselves time out at 180s (see
    # ai_agents), so the soft limit must sit above that with room for the
    # surrounding S3 downloads/uploads — 300s soft / 360s hard. (The old
    # 150s/170s were tuned when an MTU upload stall made every gptimage call
    # hang; now that that's fixed, they were cutting real renders off.)
    soft_time_limit=300,
    time_limit=360,
)
def generate_thumbnail_task(self, job_id: str) -> None:
    """Background thumbnail generation; sole argument ``job_id`` (UUID string)."""
    t0 = time.perf_counter()
    try:
        _run_async_pg(_async_generate_thumbnail(job_id, t0))
    except SoftTimeLimitExceeded:
        logger.error(
            "thumbnail.generate event=task_failed_soft_timeout job_id=%s",
            job_id,
        )
        _run_mark_pg_failed(job_id, _TIMEOUT_USER_MESSAGE)
        raise
    except Exception as exc:
        try:
            raise self.retry(exc=exc, countdown=10)
        except Retry:
            # A real retry got scheduled — let Celery's task machinery handle it.
            raise
        except Exception:
            # Retries exhausted. Depending on Celery version/config this is either
            # MaxRetriesExceededError OR `exc` itself re-raised directly — catch
            # broadly (excluding Retry above) so both cases reliably mark the job
            # failed instead of leaving it stuck at its last-known status forever.
            logger.error(
                "thumbnail.generate event=task_failed job_id=%s error=%s "
                "attempt_number=%s",
                job_id,
                _failure_log_message(exc),
                self.request.retries + 1,
            )
            _run_mark_pg_failed(job_id, _truncate_error_message(exc))
            details = mongo_repo.get_details(job_id) or {}
            capture_thumbnail_task_exhausted_retries(
                job_id,
                exc,
                self.request.retries + 1,
                details.get("model"),
            )
            return


_STALE_PROCESSING_MINUTES = 15
_STALE_TIMEOUT_MESSAGE = "Task timed out and was not cleaned up (worker killed)"


async def _reap_stale_processing_jobs() -> int:
    """Backstop for jobs orphaned by a hard-time-limit SIGKILL (SBL-17).

    The soft time limit's ``SoftTimeLimitExceeded`` handler above is
    cooperative — it only fires if the task is at a point in its execution
    where Python can receive the signal. If a task is blocked deep in a
    provider HTTP call in a way that doesn't yield back to Python promptly,
    the hard limit's SIGKILL is what actually stops it, and SIGKILL bypasses
    every Python ``except``/``finally``, leaving the job stuck in
    ``processing`` forever with no error recorded. 15 minutes is generous
    headroom above the worst case (2 attempts x (360s hard limit + 10s retry
    countdown) ~= 12.3 minutes) so this never races a job that's still
    legitimately retrying.
    """
    reaped = 0
    async with AsyncSessionLocal() as session:
        stale = await pg_repo.list_stale_processing(session, _STALE_PROCESSING_MINUTES)
        for job in stale:
            await pg_repo.update_failed(session, job["id"], _STALE_TIMEOUT_MESSAGE)
            logger.error(
                "thumbnail.generate event=reaped_stale_processing job_id=%s "
                "stuck_since=%s",
                job["id"],
                job["updated_at"],
            )
            reaped += 1
        await session.commit()
    return reaped


@celery_app.task(name="thumbnail.reap_stale_processing_jobs")
def reap_stale_processing_jobs_task() -> None:
    """Celery beat task: sweep for jobs orphaned by a hard-time-limit kill."""
    reaped = _run_async_pg(_reap_stale_processing_jobs())
    if reaped:
        logger.warning(
            "thumbnail.generate event=watchdog_reaped count=%d", reaped
        )
