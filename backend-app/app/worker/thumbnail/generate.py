"""Celery task: generate thumbnail via ``ai_agents``, upload to S3, persist state.

Flow (SBL-13): Mongo details → PG ``processing`` → ``run_thumbnail_agent`` → S3 →
Mongo ``prompt_used`` → PG ``completed``. Idempotent if already completed with
``result_url`` (SBL-13).

Retries (SBL-14): ``max_retries=2``, ``countdown=10``; final failure stores up to
500 chars in PG ``error``. Time limits (SBL-16): soft 110s / hard 120s; soft
timeout marks PG failed with a fixed message.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded

from app.celery_app import celery_app
from app.core.error_reporting import capture_thumbnail_task_exhausted_retries
from app.db.session import AsyncSessionLocal, engine
from app.repositories import mongo_repo, pg_repo
from app.services.s3_upload import get_s3_object_read_url
from app.services.thumbnail_s3 import upload_thumbnail_png

logger = logging.getLogger(__name__)

_MAX_PG_ERROR_LEN = 500
_TIMEOUT_USER_MESSAGE = "Task timed out after 110s"


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

    async def _runner() -> None:
        try:
            await coro
        finally:
            await engine.dispose(close=True)

    asyncio.run(_runner())


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
    if model not in ("gptimage", "nanobanana"):
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

    from ai_agents import run_thumbnail_agent  # deferred: requires OPENAI_API_KEY at call time

    t_agent = time.perf_counter()
    result = run_thumbnail_agent(
        model=model,
        reference_image_url=reference_image_url,
        base_image_urls=base_image_urls,
        title=details["title"],
        include_title=bool(details["include_title"]),
        creative_comments=details["creative_comments"],
    )
    agent_ms = int((time.perf_counter() - t_agent) * 1000)
    logger.info(
        "thumbnail.generate event=agent_call_completed job_id=%s model=%s "
        "duration_ms=%s",
        job_id,
        model,
        agent_ms,
    )

    raw_bytes = result.get("image_bytes")
    if not isinstance(raw_bytes, bytes | bytearray):
        raise TypeError("run_thumbnail_agent did not return bytes for image_bytes")
    image_bytes = bytes(raw_bytes)
    prompt_used = result.get("prompt_used")
    prompt_str = None if prompt_used is None else str(prompt_used)

    t_s3 = time.perf_counter()
    s3_url = upload_thumbnail_png(job_id, image_bytes)
    s3_ms = int((time.perf_counter() - t_s3) * 1000)
    logger.info(
        "thumbnail.generate event=s3_upload_completed job_id=%s model=%s "
        "duration_ms=%s",
        job_id,
        model,
        s3_ms,
    )

    if prompt_str is not None:
        mongo_repo.update_prompt_used(job_id, prompt_str)

    async with AsyncSessionLocal() as session:
        await pg_repo.update_completed(session, uid, s3_url)
        await session.commit()

    total_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(
        "thumbnail.generate event=task_completed job_id=%s model=%s "
        "total_duration_ms=%s",
        job_id,
        model,
        total_ms,
    )


@celery_app.task(
    bind=True,
    name="thumbnail.generate_thumbnail",
    max_retries=2,
    soft_time_limit=110,
    time_limit=120,
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
        except MaxRetriesExceededError:
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
