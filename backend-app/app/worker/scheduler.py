"""Celery beat task: automated YouTube batch triggering.

One task is registered:

  youtube.auto_trigger_worker  — fires hourly, 1 AM–11 PM Pacific Time
      (see beat_schedule in app.celery_app). The 1 AM tick is the daily
      kick-off, ~1 hour after the midnight-Pacific YouTube quota reset; every
      later tick keeps the queue moving.

      Each cycle it: (1) checks the day's credits aren't exhausted, (2) confirms
      no batch is currently active, then (3) dispatches the oldest pending
      (QUEUED/PAUSED) batch — exactly one per cycle. It does nothing when
      credits are exhausted, a batch is still running, or the queue is empty.

A batch that runs out of credits mid-run is left PAUSED/QUEUED, so it is simply
picked up again (oldest-first) on the next day's post-reset cycle and continues.

Duplicate-trigger safety: the orchestrator holds a Redis lock per batch and
enforces activeBatchId in daily_usage — this task only schedules; the
orchestrator rejects any race conditions.

Watchdog: each cycle first reaps a stale active batch (one whose worker died
mid-run, leaving activeBatchId set with no live run lock), so a crash/redeploy
can't deadlock the queue until the Pacific-midnight rollover.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.cache.redis_client import get_raw_redis
from app.celery_app import celery_app
from app.core.config import config
from app.core.youtube_keys import configured_youtube_key_count
from app.repositories.youtube import batch_repo, daily_usage_repo, job_log_repo
from app.schemas.youtube.batch import BatchStatus
from app.worker.orchestrator import run_batch

logger = logging.getLogger(__name__)
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_next_batch_to_trigger() -> dict | None:
    """Return the oldest QUEUED or PAUSED batch, or None if the queue is empty."""
    batches = batch_repo.list_eligible_for_trigger()
    return batches[0] if batches else None


def _credits_available() -> bool:
    """Return True when today's cumulative credit spend is below the total limit."""
    n_keys = configured_youtube_key_count()
    if n_keys == 0:
        return True  # no key configured — let orchestrator handle it

    usage = daily_usage_repo.get_today()
    if usage is None:
        return True  # no usage recorded yet → full budget available

    total_limit = config.YOUTUBE_DAILY_CREDIT_LIMIT * n_keys
    credits_used = int(usage.get("creditsUsed") or 0)
    return credits_used < total_limit


def _credits_remaining() -> int:
    """Return approximate credits left across all API keys for today."""
    n_keys = configured_youtube_key_count()
    total_limit = config.YOUTUBE_DAILY_CREDIT_LIMIT * n_keys
    usage = daily_usage_repo.get_today()
    credits_used = int((usage or {}).get("creditsUsed") or 0)
    return max(0, total_limit - credits_used)


def _reap_stale_active_batch() -> None:
    """Recover from a worker that died mid-run (watchdog).

    If ``activeBatchId`` is set but the batch's run lock (``batch_lock:{id}``) is
    gone, the orchestrator is no longer running it — the worker crashed or was
    redeployed between marking the batch RUNNING and finalising it. Without this,
    ``activeBatchId`` would stay set (Guard 2 below) and block every auto-trigger
    until the Pacific-midnight daily_usage rollover — a ~23h queue deadlock.

    The orchestrator renews the lock after every term, so a live lock means a run
    is genuinely in progress and we leave it alone. A missing lock means the run
    is orphaned: reset the batch to PAUSED (so it re-queues) and clear the flag.
    """
    usage = daily_usage_repo.get_today()
    active = (usage or {}).get("activeBatchId")
    if not active:
        return

    if get_raw_redis().get(f"batch_lock:{active}") is not None:
        return  # lock alive → a run is really in progress; not stale

    logger.warning(
        "auto_trigger_worker: active batch %s has no run lock — worker died mid-run; recovering",
        active,
    )
    batch = batch_repo.get_by_id(active)
    if batch and batch.get("status") == BatchStatus.RUNNING.value:
        batch_repo.update_status(active, BatchStatus.PAUSED)
        job_log_repo.append(
            active,
            "run_reaped",
            "Auto-recovered by watchdog: worker died mid-run; batch reset to PAUSED for retry.",
        )
    daily_usage_repo.clear_active_batch()


def _dispatch(batch: dict, trigger_source: str) -> None:
    """Log and enqueue a batch run."""
    batch_id = str(batch["_id"])
    credits_remaining = _credits_remaining()
    now_iso = datetime.now(PACIFIC_TZ).isoformat()

    logger.info(
        "scheduler[%s]: triggering batch %s (%r) at %s | credits_remaining=%d",
        trigger_source,
        batch_id,
        batch.get("name"),
        now_iso,
        credits_remaining,
    )

    job_log_repo.append(
        batch_id,
        "auto_trigger",
        (
            f"Auto-triggered by {trigger_source} at {now_iso}. "
            f"Credits remaining: {credits_remaining}"
        ),
    )

    run_batch.delay(batch_id)


# ── Celery beat task ──────────────────────────────────────────────────────────


@celery_app.task(name="youtube.auto_trigger_worker", bind=True)
def auto_trigger_batch_worker(self) -> None:  # noqa: ANN001
    """Hourly (1 AM–11 PM PT): advance the batch queue by one batch per cycle."""

    # --- Watchdog: recover a batch orphaned by a dead worker ---
    _reap_stale_active_batch()

    # --- Guard 1: credits exhausted ---
    if not _credits_available():
        logger.info("auto_trigger_worker: credits exhausted for today, skipping cycle")
        return

    # --- Guard 2: a batch is already actively running ---
    usage = daily_usage_repo.get_today()
    if usage and usage.get("activeBatchId"):
        logger.info(
            "auto_trigger_worker: batch %s is active, waiting for it to finish",
            usage["activeBatchId"],
        )
        return

    # --- Find and dispatch the next batch ---
    batch = _get_next_batch_to_trigger()
    if batch is None:
        logger.info("auto_trigger_worker: queue empty, nothing to trigger")
        return

    _dispatch(batch, "hourly_worker")
