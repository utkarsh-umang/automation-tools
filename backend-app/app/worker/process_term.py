"""Celery task: process a single search term.

process_term(batch_id, term_id, credit_key) performs the full pipeline
for one search term:
  1. Mark term running
  2. collect_channel_ids → channel ID pool
  3. get_channel_details_batch → full channel data
  4. evaluate_channel for each → qualified leads accumulated in memory
  5. insert_many leads atomically
  6. mark term done with stats

On any unhandled exception the term is marked failed and the error is
logged to yt_job_logs.  CreditLimitExceeded is re-raised so the
orchestrator can roll back the term and pause the batch.
"""

import logging
from datetime import datetime

from app.cache.redis_client import get_raw_redis
from app.celery_app import celery_app
from app.core.config import config
from app.repositories.youtube import (
    batch_repo,
    job_log_repo,
    lead_repo,
    search_term_repo,
)
from app.worker.youtube.channels import get_channel_details_batch
from app.worker.youtube.credits import CreditCounter, CreditLimitExceeded
from app.worker.youtube.evaluate import evaluate_channel
from app.worker.youtube.search import collect_channel_ids

logger = logging.getLogger(__name__)


@celery_app.task(name="youtube.process_term", bind=True)
def process_term(self, batch_id: str, term_id: str, credit_key: str) -> int:
    """Process a single search term end-to-end.

    Returns the number of credits used during this task (delta from
    before the call).  The orchestrator persists this to daily_usage.
    """
    redis_client = get_raw_redis()
    counter = CreditCounter(redis_client, credit_key)  # uses existing Redis value

    credits_before = counter.total()

    term_doc = search_term_repo.get_by_id(term_id)
    if term_doc is None:
        raise ValueError(f"SearchTerm {term_id} not found")

    batch_doc = batch_repo.get_by_id(batch_id)
    if batch_doc is None:
        raise ValueError(f"Batch {batch_id} not found")

    filters = batch_doc.get("filters", {})
    keyword = term_doc["term"]
    api_key = config.YOUTUBE_API_KEY_V3

    search_term_repo.mark_running(term_id)
    job_log_repo.append(batch_id, "term_started", f"Processing term: {keyword}", term_id)

    try:
        # ── Step 1: collect channel IDs ────────────────────────────────
        channel_ids = collect_channel_ids(
            keyword=keyword,
            api_key=api_key,
            counter=counter,
            credit_limit=config.YOUTUBE_DAILY_CREDIT_LIMIT,
            region=filters.get("region", "US"),
        )
        channels_discovered = len(channel_ids)
        logger.info(
            "process_term: term=%r discovered %d channels", keyword, channels_discovered
        )

        # ── Step 2: fetch channel details ─────────────────────────────
        channels_data = get_channel_details_batch(channel_ids, api_key, counter)

        # ── Step 3: evaluate and accumulate leads ─────────────────────
        leads: list[dict] = []
        emails_found = 0

        for channel in channels_data:
            lead = evaluate_channel(channel, filters, api_key, counter)
            if lead is None:
                continue
            lead["batchId"] = batch_id
            lead["searchTermId"] = term_id
            lead["discoveredAt"] = datetime.utcnow()
            leads.append(lead)
            if lead.get("emailStatus") == "found":
                emails_found += 1

        channels_qualified = len(leads)

        # ── Step 4: bulk insert leads (atomic — no partial writes) ────
        lead_repo.insert_many(leads)

        # ── Step 5: mark term done ────────────────────────────────────
        credits_used = counter.total() - credits_before
        search_term_repo.mark_done(
            term_id,
            credits_used=credits_used,
            channels_discovered=channels_discovered,
            channels_qualified=channels_qualified,
            emails_found=emails_found,
        )
        batch_repo.increment_processed_terms(batch_id)

        job_log_repo.append(
            batch_id,
            "term_done",
            (
                f"Term '{keyword}' done. "
                f"discovered={channels_discovered} qualified={channels_qualified} "
                f"emails={emails_found} credits={credits_used}"
            ),
            term_id,
        )

        logger.info(
            "process_term done: term=%r qualified=%d credits_used=%d",
            keyword,
            channels_qualified,
            credits_used,
        )
        return credits_used

    except CreditLimitExceeded:
        # Orchestrator handles rollback — just re-raise
        raise

    except Exception as exc:
        error_msg = str(exc)
        logger.exception("process_term failed for term=%r: %s", keyword, error_msg)
        search_term_repo.mark_failed(term_id, error_msg)
        job_log_repo.append(batch_id, "term_failed", f"Term '{keyword}' failed: {error_msg}", term_id)
        raise
