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
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # Fire once daily at 1:00 PM IST (07:30 UTC) to kick off the first batch.
        "auto-trigger-batch-daily": {
            "task": "youtube.auto_trigger_daily",
            "schedule": crontab(hour=7, minute=30),
        },
        # Poll every 2 minutes to advance the queue after the first batch finishes.
        "auto-trigger-batch-worker": {
            "task": "youtube.auto_trigger_worker",
            "schedule": crontab(minute="*/2"),
        },
    },
)
