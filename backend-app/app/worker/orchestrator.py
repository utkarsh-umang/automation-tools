"""Celery task: orchestrate a full batch run.

run_batch(batch_id) manages the batch state machine:

    queued/paused → running → [term loop] → completed / paused / failed

Key behaviours:
  - Redis distributed lock prevents double-trigger (key: batch_lock:{batch_id})
  - One-batch-per-day enforced via daily_usage.activeBatchId
  - Per-key credit counters initialised from persisted daily_usage at run start
  - Terms processed sequentially; credit limit hit on last key → term rolled back, batch paused
  - Single term failure does not stop the batch (logs error, moves on)
  - Lock always released in finally block
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.cache.redis_client import get_raw_redis
from app.celery_app import celery_app
from app.core.config import config
from app.core.youtube_keys import get_ordered_youtube_api_keys
from app.repositories.youtube import (
    batch_repo,
    daily_usage_repo,
    job_log_repo,
    search_term_repo,
)
from app.schemas.youtube.batch import BatchStatus
from app.worker.process_term import process_term
from app.worker.youtube.credits import CreditLimitExceeded
from app.worker.youtube.quota_context import (
    aggregate_from_redis,
    all_keys_exhausted,
    seed_redis_from_mongo,
)

logger = logging.getLogger(__name__)

LOCK_TTL_SECONDS = 600  # 10 minutes
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


@celery_app.task(name="youtube.run_batch", bind=True, acks_late=True)
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


def _normalise_credits_by_key(usage: dict, num_keys: int) -> dict[str, int]:
    """Build per-key seed from Mongo; migrate legacy single ``creditsUsed`` to key 0."""
    raw = usage.get("creditsByKey")
    if isinstance(raw, dict) and raw:
        return {str(i): int(raw.get(str(i), 0)) for i in range(num_keys)}
    legacy = int(usage.get("creditsUsed") or 0)
    return {str(i): (legacy if i == 0 else 0) for i in range(num_keys)}


def _run(batch_id: str, redis_client) -> None:  # noqa: ANN001
    """Inner run logic (separated from the lock boilerplate for clarity)."""
    today = datetime.now(PACIFIC_TZ).date().isoformat()
    lock_key = f"batch_lock:{batch_id}"

    try:
        api_keys = get_ordered_youtube_api_keys()
    except ValueError as exc:
        logger.error("run_batch: %s — marking batch %s as failed", exc, batch_id)
        batch_repo.update_status(batch_id, BatchStatus.FAILED)
        job_log_repo.append(batch_id, "run_failed", str(exc))
        return

    n_keys = len(api_keys)
    per_limit = config.YOUTUBE_DAILY_CREDIT_LIMIT

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

    # ── Initialise per-key Redis counters from persisted usage ────────
    credits_by_key = _normalise_credits_by_key(usage, n_keys)
    seed_redis_from_mongo(redis_client, today, n_keys, credits_by_key)
    credits_at_start, _ = aggregate_from_redis(redis_client, today, n_keys)

    if all_keys_exhausted(redis_client, today, n_keys, per_limit):
        logger.info("run_batch: daily credit limit already reached on all keys, pausing batch %s", batch_id)
        batch_repo.update_status(batch_id, BatchStatus.PAUSED)
        job_log_repo.append(batch_id, "run_paused", "Daily credit limit already reached (all keys)")
        return

    # ── Mark batch running ────────────────────────────────────────────
    batch_repo.update_status(
        batch_id,
        BatchStatus.RUNNING,
        last_triggered_at=datetime.utcnow(),
    )
    daily_usage_repo.set_active_batch(batch_id)

    job_log_repo.append(
        batch_id,
        "run_started",
        f"Batch run started. Credits at start (all keys): {credits_at_start}",
    )

    # ── Process pending terms sequentially ───────────────────────────
    pending_terms = search_term_repo.get_pending_for_batch(batch_id)

    if not pending_terms:
        logger.info("run_batch: no pending terms for batch %s", batch_id)
        _finalise(batch_id, redis_client, today, n_keys, credits_at_start)
        return

    credit_limit_hit = False

    for term_doc in pending_terms:
        term_id = term_doc["_id"]
        keyword = term_doc.get("term", "")

        if all_keys_exhausted(redis_client, today, n_keys, per_limit):
            logger.info(
                "run_batch: credit limit reached on all keys before term %s (%r), pausing",
                term_id,
                keyword,
            )
            credit_limit_hit = True
            break

        try:
            # Run term processing inline to guarantee exception propagation.
            # Using Celery's Task.apply() can return a failure result without raising,
            # which breaks the credit-limit pause/rollback behavior.
            process_term(batch_id, term_id, today)
        except CreditLimitExceeded:
            logger.info(
                "run_batch: credit limit hit mid-term %s (%r), rolling back to pending",
                term_id,
                keyword,
            )
            search_term_repo.reset_to_pending(term_id)
            credit_limit_hit = True
            break
        except Exception as exc:
            logger.exception(
                "run_batch: term %s (%r) failed with: %s", term_id, keyword, exc
            )
            # Mark is already done by process_term; continue to next term

        total, by_key = aggregate_from_redis(redis_client, today, n_keys)
        daily_usage_repo.set_credits_used_and_by_key(total, by_key)

        # Heartbeat: renew the run lock after each term so it stays alive for the
        # whole (potentially long) run. The scheduler treats a live lock as
        # proof the worker is still running; if the worker dies, the lock lapses
        # (≤ LOCK_TTL_SECONDS) and the scheduler's reaper recovers the batch.
        redis_client.expire(lock_key, LOCK_TTL_SECONDS)

    total, by_key = aggregate_from_redis(redis_client, today, n_keys)
    daily_usage_repo.set_credits_used_and_by_key(total, by_key)

    if credit_limit_hit:
        batch_repo.update_status(batch_id, BatchStatus.PAUSED)
        daily_usage_repo.clear_active_batch()
        job_log_repo.append(
            batch_id,
            "run_paused",
            f"Daily credit limit reached (last key). Credits used: {total}",
        )
        logger.info(
            "run_batch: batch %s paused (credit limit). Total credits: %d",
            batch_id,
            total,
        )
        return

    _finalise(batch_id, redis_client, today, n_keys, credits_at_start)


def _finalise(
    batch_id: str,
    redis_client,
    today: str,
    n_keys: int,
    credits_at_start: int,
) -> None:
    """Determine final batch status after all terms are processed."""
    terms = search_term_repo.get_all_for_batch(batch_id)
    statuses = {t["status"] for t in terms}

    # If any term remains pending/running, the batch is not complete.
    # This protects against early termination (crash/timeout/quota stop)
    # leaving terms incomplete, and prevents incorrectly marking a batch as completed.
    if "pending" in statuses or "running" in statuses:
        batch_repo.update_status(batch_id, BatchStatus.PAUSED)
        status_label = "paused (incomplete terms remain)"
    elif not statuses or statuses == {"done"}:
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

    total, _by = aggregate_from_redis(redis_client, today, n_keys)
    credits_this_run = total - credits_at_start
    job_log_repo.append(
        batch_id,
        "run_completed",
        (
            f"Batch {status_label}. "
            f"Credits this run: {credits_this_run}. "
            f"Total today: {total}"
        ),
    )
    logger.info(
        "run_batch: batch %s %s. credits_this_run=%d total_today=%d",
        batch_id,
        status_label,
        credits_this_run,
        total,
    )
