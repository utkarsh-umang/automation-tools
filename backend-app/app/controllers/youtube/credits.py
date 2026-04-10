"""Routes: YouTube daily credit usage.

GET /api/v1/youtube/credits/today
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter

from app.core.config import config
from app.core.youtube_keys import configured_youtube_key_count, youtube_key_labels_for_ui
from app.repositories.youtube import daily_usage_repo

router = APIRouter()
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


@router.get("/today")
def get_credits_today() -> dict:
    """Return today's YouTube API credit usage.

    Returns a zeroed response (not 404) if no usage has been recorded yet.
    resetAt is midnight Pacific Time of the following day.

    ``keys`` lists per-key usage when multiple keys are configured; raw API key
    strings are never returned.
    """
    usage = daily_usage_repo.get_today()

    per_key_limit = config.YOUTUBE_DAILY_CREDIT_LIMIT
    n_keys = configured_youtube_key_count()
    labels = youtube_key_labels_for_ui()

    credits_by_key: dict[str, int] = {}
    if usage and isinstance(usage.get("creditsByKey"), dict):
        credits_by_key = {str(k): int(v) for k, v in usage["creditsByKey"].items()}

    legacy_used = int(usage.get("creditsUsed", 0)) if usage else 0

    if n_keys == 0:
        used = legacy_used
        limit_total = per_key_limit
        keys_out: list[dict] = []
    else:
        keys_out = []
        used = 0
        for i in range(n_keys):
            if credits_by_key:
                u = int(credits_by_key.get(str(i), 0))
            else:
                u = legacy_used if i == 0 else 0
            used += u
            rem = max(0, per_key_limit - u)
            keys_out.append(
                {
                    "id": str(i),
                    "label": labels[i] if i < len(labels) else f"Key {i + 1}",
                    "used": u,
                    "limit": per_key_limit,
                    "remaining": rem,
                }
            )
        limit_total = per_key_limit * n_keys

    remaining = max(0, limit_total - used)
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
        "remaining": remaining,
        "limit": limit_total,
        "activeBatchId": active_batch_id,
        "resetAt": reset_at,
        "keys": keys_out,
    }
