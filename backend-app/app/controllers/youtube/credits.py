"""Routes: YouTube daily credit usage.

GET /api/v1/youtube/credits/today
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter

from app.core.config import config
from app.repositories.youtube import daily_usage_repo

router = APIRouter()
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


@router.get("/today")
def get_credits_today() -> dict:
    """Return today's YouTube API credit usage.

    Returns a zeroed response (not 404) if no usage has been recorded yet.
    resetAt is midnight Pacific Time of the following day.
    """
    usage = daily_usage_repo.get_today()

    used = usage.get("creditsUsed", 0) if usage else 0
    limit = usage.get("creditLimit", config.YOUTUBE_DAILY_CREDIT_LIMIT) if usage else config.YOUTUBE_DAILY_CREDIT_LIMIT
    active_batch_id = usage.get("activeBatchId") if usage else None

    now_pt = datetime.now(PACIFIC_TZ)
    tomorrow_pt = now_pt.date() + timedelta(days=1)
    reset_at = datetime(
        tomorrow_pt.year,
        tomorrow_pt.month,
        tomorrow_pt.day,
        0,
        0,
        0,
        tzinfo=PACIFIC_TZ,
    ).isoformat()

    return {
        "used": used,
        "remaining": max(0, limit - used),
        "limit": limit,
        "activeBatchId": active_batch_id,
        "resetAt": reset_at,
    }
