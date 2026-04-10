"""Channel evaluation and email extraction.

Ported from youtube_script.py:
  - extract_emails()
  - evaluate_channel()

All global variables replaced with a `filters` dict so the batch's
filter settings drive evaluation dynamically.
"""

import logging
import math
import re
from datetime import datetime, timedelta

from app.schemas.youtube.lead import EmailStatus
from app.worker.youtube.channels import get_recent_videos, get_video_stats
from app.worker.youtube.credits import CreditLimitExceeded
from app.worker.youtube.quota_context import YouTubeQuotaContext

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}")


def extract_emails(text: str) -> list[str]:
    """Extract unique email addresses from a text block."""
    if not text:
        return []
    return list(set(EMAIL_REGEX.findall(text)))


def evaluate_channel(
    channel: dict,
    filters: dict,
    quota: YouTubeQuotaContext,
) -> dict | None:
    """Evaluate a single channel against the batch's filter criteria.

    Returns a lead-shaped dict on pass, None if the channel is filtered out.

    filters keys (all match BatchFilters schema):
        minSubs, maxSubs, minUploadsLast30d, minAvgViews,
        excludeCountries, region
    """
    try:
        subs = int(channel.get("statistics", {}).get("subscriberCount", 0))
        if subs < filters.get("minSubs", 0) or subs > filters.get("maxSubs", 10_000_000):
            return None

        country = channel.get("snippet", {}).get("country", "")
        exclude_countries = filters.get("excludeCountries", ["IN"])
        if country in exclude_countries:
            return None

        video_count = int(channel.get("statistics", {}).get("videoCount", 0))
        if video_count < 20:
            return None

        uploads_playlist = (
            channel.get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads", "")
        )
        if not uploads_playlist:
            return None

        videos = get_recent_videos(uploads_playlist, quota)

        cutoff = datetime.utcnow() - timedelta(days=30)
        recent_count = 0
        video_ids: list[str] = []
        last_upload_date: datetime | None = None

        for vid in videos:
            snippet = vid.get("snippet", {})
            published_raw = snippet.get("publishedAt", "")
            try:
                published = datetime.strptime(published_raw, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue

            if last_upload_date is None:
                last_upload_date = published

            if published > cutoff:
                recent_count += 1

            video_id = snippet.get("resourceId", {}).get("videoId", "")
            if video_id:
                video_ids.append(video_id)

        min_uploads = filters.get("minUploadsLast30d", 1)
        if recent_count < min_uploads:
            return None

        stats = get_video_stats(video_ids[:20], quota)
        views = [int(v.get("statistics", {}).get("viewCount", 0)) for v in stats]
        avg_views = sum(views) / len(views) if views else 0

        min_avg_views = filters.get("minAvgViews", 0)
        if avg_views < min_avg_views:
            return None

        description = channel.get("snippet", {}).get("description", "")
        emails = extract_emails(description)

        if emails:
            email_value = ",".join(emails)
            email_status = EmailStatus.FOUND
        elif "business" in description.lower() or "contact" in description.lower():
            email_value = ""
            email_status = EmailStatus.CAPTCHA
        else:
            email_value = ""
            email_status = EmailStatus.NONE

        score = (
            recent_count * 3
            + math.log10(subs + 1) * 2
            + (avg_views / 10_000)
        )

        channel_id = channel.get("id", "")
        return {
            "channelName": channel.get("snippet", {}).get("title", ""),
            "channelUrl": f"https://youtube.com/channel/{channel_id}",
            "channelId": channel_id,
            "subscribers": subs,
            "uploadsLast30d": recent_count,
            "avgViews": int(avg_views),
            "lastUpload": last_upload_date.strftime("%Y-%m-%d") if last_upload_date else None,
            "score": round(score, 2),
            "country": country,
            "email": email_value,
            "emailStatus": email_status.value,
        }

    except CreditLimitExceeded:
        raise
    except Exception as exc:
        logger.warning("evaluate_channel error for channel %s: %s", channel.get("id"), exc)
        return None
