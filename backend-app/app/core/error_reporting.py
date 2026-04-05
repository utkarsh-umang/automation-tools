"""Optional Sentry reporting for terminal failures (lazy import, never raises)."""

from __future__ import annotations

import logging

from app.core.config import config

logger = logging.getLogger(__name__)


def capture_thumbnail_task_exhausted_retries(
    job_id: str,
    exc: BaseException,
    attempt_number: int,
    model: str | None,
) -> None:
    """Send exception to Sentry when DSN is configured; safe if sentry_sdk is absent."""
    dsn = (config.SENTRY_DSN or "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk
    except ImportError:
        logger.warning(
            "thumbnail.error_reporting event=sentry_sdk_missing job_id=%s",
            job_id,
        )
        return

    with sentry_sdk.push_scope() as scope:  # type: ignore[union-attr]
        scope.set_tag("job_id", job_id)
        scope.set_tag("model", model or "unknown")
        scope.set_tag("attempt_number", str(attempt_number))
        sentry_sdk.capture_exception(exc)  # type: ignore[union-attr]
