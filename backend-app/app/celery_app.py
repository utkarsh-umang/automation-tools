"""Celery application (broker/result: Redis)."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import config

celery_app = Celery(
    "backend",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_BROKER_URL,
    include=[
        "app.worker.orchestrator",
        "app.worker.process_term",
        "app.worker.thumbnail.generate",
        "app.worker.scheduler",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # YouTube Data API v3 quota resets at midnight Pacific Time. We schedule in
    # Pacific so the trigger tracks the reset automatically across US daylight
    # saving (no need to re-tune UTC offsets twice a year).
    timezone="America/Los_Angeles",
    enable_utc=True,
    beat_schedule={
        # Advance the YouTube batch queue every hour, on the hour, from 1 AM to
        # 11 PM Pacific. The 1 AM tick is the daily kick-off: it fires ~1 hour
        # after the midnight-Pacific quota reset (safety margin for Google to
        # actually reset), dispatching the oldest pending batch. Every later
        # tick drains the queue — if the previous batch finished and credits
        # remain, it dispatches the next one (one batch per tick). Midnight
        # (hour 0) is intentionally skipped so we never run on the old day's
        # exhausted quota just before the reset.
        "auto-trigger-batch-worker": {
            "task": "youtube.auto_trigger_worker",
            "schedule": crontab(minute=0, hour="1-23"),
        },
        # Reap thumbnail jobs orphaned by a hard-time-limit SIGKILL (the soft
        # limit's cooperative cleanup can't always run — see generate.py).
        # Every 5 minutes is frequent enough that a stuck job never sits
        # unexplained for long, cheap enough (one indexed query, usually
        # zero rows) to not matter at this interval.
        "reap-stale-thumbnail-jobs": {
            "task": "thumbnail.reap_stale_processing_jobs",
            "schedule": crontab(minute="*/5"),
        },
    },
)
