"""Celery task: orchestrate a full batch run.

run_batch(batch_id) manages the batch state machine:

    queued/paused → running → [term loop] → completed / paused / failed

Key behaviours:
  - Redis distributed lock prevents double-trigger (key: batch_lock:{batch_id})
  - One-batch-per-day enforced via daily_usage.activeBatchId
  - Credit counter initialised from persisted daily_usage at run start
  - Terms processed sequentially; credit limit hit → term rolled back, batch paused
  - Single term failure does not stop the batch (logs error, moves on)
  - Lock always released in finally block
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.cache.redis_client import get_raw_redis
from app.celery_app import celery_app
from app.core.config import config
from app.repositories.youtube import (
    batch_repo,
    daily_usage_repo,
    job_log_repo,
    search_term_repo,
)
from app.schemas.youtube.batch import BatchStatus
from app.worker.process_term import process_term
from app.worker.youtube.credits import CreditCounter, CreditLimitExceeded

logger = logging.getLogger(__name__)

LOCK_TTL_SECONDS = 600  # 10 minutes
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


@celery_app.task(name="youtube.run_batch", bind=True)
def run_batch(self, batch_id: str) -> None:
    """Orchestrate all pending terms in a batch for today's run."""
    redis_client = get_raw_redis()
    lock_key = f"batch_lock:{batch_id}"

    # ── Acquire distributed lock ──────────────────────────────────────
    acquired = redis_client.set(lock_key, "1", nx=True, ex=LOCK_TTL_SECONDS)
    if not acquired:
        logger.warning("run_batch: could not acquire lock for batch %s", batch_id)
        return

    try:
        _run(batch_id, redis_client)
    finally:
        redis_client.delete(lock_key)
        logger.info("run_batch: lock released for batch %s", batch_id)


def _run(batch_id: str, redis_client) -> None:  # noqa: ANN001
    """Inner run logic (separated from the lock boilerplate for clarity)."""
    today = datetime.now(PACIFIC_TZ).date().isoformat()
    credit_key = f"yt_credits:{today}"

    # ── Check batch is in a triggerable state ─────────────────────────
    batch = batch_repo.get_by_id(batch_id)
    if batch is None:
        logger.error("run_batch: batch %s not found", batch_id)
        return

    if batch["status"] not in (BatchStatus.QUEUED.value, BatchStatus.PAUSED.value):
        logger.warning(
            "run_batch: batch %s is in status %s, skipping",
            batch_id,
            batch["status"],
        )
        return

    # ── Check daily one-batch-per-day rule ────────────────────────────
    usage = daily_usage_repo.get_or_create_today()
    active = usage.get("activeBatchId")
    if active and active != batch_id:
        logger.warning(
            "run_batch: another batch (%s) is already active today, aborting %s",
            active,
            batch_id,
        )
        job_log_repo.append(
            batch_id,
            "run_blocked",
            f"Another batch ({active}) is already running today",
        )
        return

    # ── Initialise credit counter from today's persisted usage ────────
    credits_at_start = usage.get("creditsUsed", 0)
    counter = CreditCounter(redis_client, credit_key, initial=credits_at_start)

    # Immediately check whether we are already over limit
    if counter.over_limit(config.YOUTUBE_DAILY_CREDIT_LIMIT):
        logger.info("run_batch: daily credit limit already reached, pausing batch %s", batch_id)
        batch_repo.update_status(batch_id, BatchStatus.PAUSED)
        job_log_repo.append(batch_id, "run_paused", "Daily credit limit already reached")
        return

    # ── Mark batch running ────────────────────────────────────────────
    batch_repo.update_status(
        batch_id,
        BatchStatus.RUNNING,
        last_triggered_at=__import__("datetime").datetime.utcnow(),
    )
    daily_usage_repo.set_active_batch(batch_id)

    job_log_repo.append(
        batch_id,
        "run_started",
        f"Batch run started. Credits at start: {credits_at_start}",
    )

    # ── Process pending terms sequentially ───────────────────────────
    pending_terms = search_term_repo.get_pending_for_batch(batch_id)

    if not pending_terms:
        logger.info("run_batch: no pending terms for batch %s", batch_id)
        _finalise(batch_id, counter, credits_at_start)
        return

    credit_limit_hit = False

    for term_doc in pending_terms:
        term_id = term_doc["_id"]
        keyword = term_doc.get("term", "")

        # Pre-term credit check
        if counter.over_limit(config.YOUTUBE_DAILY_CREDIT_LIMIT):
            logger.info(
                "run_batch: credit limit reached before term %s (%r), pausing",
                term_id,
                keyword,
            )
            credit_limit_hit = True
            break

        try:
            process_term.apply(args=[batch_id, term_id, credit_key])
        except CreditLimitExceeded:
            logger.info(
                "run_batch: credit limit hit mid-term %s (%r), rolling back to pending",
                term_id,
                keyword,
            )
            search_term_repo.reset_to_pending(term_id)
            batch_repo.increment_processed_terms.__doc__  # noop — do NOT increment for rolled-back term
            credit_limit_hit = True
            break
        except Exception as exc:
            logger.exception(
                "run_batch: term %s (%r) failed with: %s", term_id, keyword, exc
            )
            # Mark is already done by process_term; continue to next term

        # Persist credit total to MongoDB after each term
        daily_usage_repo.set_credits_used(counter.total())

    # Final credit persist
    daily_usage_repo.set_credits_used(counter.total())

    if credit_limit_hit:
        batch_repo.update_status(batch_id, BatchStatus.PAUSED)
        daily_usage_repo.clear_active_batch()
        job_log_repo.append(
            batch_id,
            "run_paused",
            f"Daily credit limit reached. Credits used: {counter.total()}",
        )
        logger.info(
            "run_batch: batch %s paused (credit limit). Total credits: %d",
            batch_id,
            counter.total(),
        )
        return

    _finalise(batch_id, counter, credits_at_start)


def _finalise(batch_id: str, counter: CreditCounter, credits_at_start: int) -> None:
    """Determine final batch status after all terms are processed."""
    terms = search_term_repo.get_all_for_batch(batch_id)
    statuses = {t["status"] for t in terms}

    from datetime import datetime

    if not statuses or statuses == {"done"}:
        batch_repo.update_status(
            batch_id, BatchStatus.COMPLETED, completed_at=datetime.utcnow()
        )
        status_label = "completed"
    elif statuses == {"failed"}:
        batch_repo.update_status(batch_id, BatchStatus.FAILED)
        status_label = "failed"
    else:
        # Mix of done and failed — mark completed (visible failed terms in Flower)
        batch_repo.update_status(
            batch_id, BatchStatus.COMPLETED, completed_at=datetime.utcnow()
        )
        status_label = "completed (with failures)"

    daily_usage_repo.clear_active_batch()
    daily_usage_repo.increment_runs()

    credits_this_run = counter.total() - credits_at_start
    job_log_repo.append(
        batch_id,
        "run_completed",
        (
            f"Batch {status_label}. "
            f"Credits this run: {credits_this_run}. "
            f"Total today: {counter.total()}"
        ),
    )
    logger.info(
        "run_batch: batch %s %s. credits_this_run=%d total_today=%d",
        batch_id,
        status_label,
        credits_this_run,
        counter.total(),
    )
