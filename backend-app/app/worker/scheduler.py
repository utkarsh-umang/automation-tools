"""Celery beat tasks: automated daily YouTube batch triggering.

Two tasks are registered:

  youtube.auto_trigger_daily   — fires once at 1:00 PM UTC every day.
      Finds the oldest QUEUED/PAUSED batch and dispatches it.

  youtube.auto_trigger_worker  — fires every 2 minutes.
      After the daily session has started, this keeps the queue moving:
      it checks remaining credits, confirms no batch is currently active,
      and dispatches the next oldest pending batch (exactly one per cycle).
      Does nothing when credits are exhausted or the queue is empty.

Duplicate-trigger safety: the orchestrator holds a Redis lock per batch and
enforces activeBatchId in daily_usage — these tasks only schedule; the
orchestrator rejects any race conditions.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.celery_app import celery_app
from app.core.config import config
from app.core.youtube_keys import configured_youtube_key_count
from app.repositories.youtube import batch_repo, daily_usage_repo, job_log_repo
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


# ── Celery beat tasks ─────────────────────────────────────────────────────────


@celery_app.task(name="youtube.auto_trigger_daily", bind=True)
def auto_trigger_batch_daily(self) -> None:  # noqa: ANN001
    """1 PM UTC daily kick-off: dispatch the oldest pending batch."""
    logger.info("auto_trigger_daily: daily scheduler fired")

    if not _credits_available():
        logger.info("auto_trigger_daily: credits exhausted for today, skipping")
        return

    batch = _get_next_batch_to_trigger()
    if batch is None:
        logger.info("auto_trigger_daily: no eligible batches in queue, skipping")
        return

    _dispatch(batch, "daily_scheduler")


@celery_app.task(name="youtube.auto_trigger_worker", bind=True)
def auto_trigger_batch_worker(self) -> None:  # noqa: ANN001
    """Every-2-minute worker: advance the batch queue by one batch per cycle."""

    # --- Guard 1: credits exhausted ---
    if not _credits_available():
        logger.debug("auto_trigger_worker: credits exhausted, skipping cycle")
        return

    # --- Guard 2: a batch is already actively running ---
    usage = daily_usage_repo.get_today()
    if usage and usage.get("activeBatchId"):
        logger.debug(
            "auto_trigger_worker: batch %s is active, waiting for it to finish",
            usage["activeBatchId"],
        )
        return

    # --- Find and dispatch the next batch ---
    batch = _get_next_batch_to_trigger()
    if batch is None:
        logger.debug("auto_trigger_worker: queue empty, nothing to trigger")
        return

    _dispatch(batch, "2min_worker")
