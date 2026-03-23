"""Routes: YouTube daily credit usage.

GET /api/v1/youtube/credits/today
"""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter

from app.core.config import config
from app.repositories.youtube import daily_usage_repo

router = APIRouter()


@router.get("/today")
def get_credits_today() -> dict:
    """Return today's YouTube API credit usage.

    Returns a zeroed response (not 404) if no usage has been recorded yet.
    resetAt is midnight UTC of the following day.
    """
    usage = daily_usage_repo.get_today()

    used = usage.get("creditsUsed", 0) if usage else 0
    limit = usage.get("creditLimit", config.YOUTUBE_DAILY_CREDIT_LIMIT) if usage else config.YOUTUBE_DAILY_CREDIT_LIMIT
    active_batch_id = usage.get("activeBatchId") if usage else None

    tomorrow = date.today() + timedelta(days=1)
    reset_at = datetime(
        tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0, tzinfo=UTC
    ).isoformat()

    return {
        "used": used,
        "remaining": max(0, limit - used),
        "limit": limit,
        "activeBatchId": active_batch_id,
        "resetAt": reset_at,
    }
