"""Celery application (broker/result: Redis)."""

from celery import Celery

from app.core.config import config

celery_app = Celery(
    "backend",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_BROKER_URL,
    include=[
        "app.worker.orchestrator",
        "app.worker.process_term",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
