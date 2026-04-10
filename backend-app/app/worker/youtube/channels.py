"""YouTube channel detail fetching helpers.

Ported from youtube_script.py:
  - get_channel_details_batch()
  - get_recent_videos()
  - get_video_stats()

Each function accepts :class:`YouTubeQuotaContext` for key selection and credits.
Credit cost: 1 credit per API call (channels, playlistItems, videos).
"""

import logging
import time

import requests

from app.worker.youtube.quota_context import YouTubeQuotaContext

logger = logging.getLogger(__name__)

BASE_URL = "https://www.googleapis.com/youtube/v3"
CHANNEL_BATCH_SIZE = 50
CHANNEL_CREDIT_COST = 1
PLAYLIST_CREDIT_COST = 1
VIDEO_CREDIT_COST = 1


def get_channel_details_batch(
    channel_ids: list[str],
    quota: YouTubeQuotaContext,
) -> list[dict]:
    """Fetch full channel details (statistics, snippet, contentDetails) in batches of 50.

    Returns the raw list of channel items from the YouTube API.
    Cost: 1 credit per batch of 50 channel IDs.
    """
    channels_data: list[dict] = []

    for i in range(0, len(channel_ids), CHANNEL_BATCH_SIZE):
        batch = channel_ids[i : i + CHANNEL_BATCH_SIZE]
        api_key, counter = quota.prepare_for_charge(CHANNEL_CREDIT_COST)
        params = {
            "part": "statistics,contentDetails,snippet",
            "id": ",".join(batch),
            "key": api_key,
        }
        try:
            res = requests.get(f"{BASE_URL}/channels", params=params, timeout=15).json()
        except Exception as exc:
            logger.warning("channels API request failed for batch %d: %s", i, exc)
            continue

        counter.add(CHANNEL_CREDIT_COST)
        channels_data.extend(res.get("items", []))
        time.sleep(0.2)

    logger.debug("get_channel_details_batch: fetched %d channel records", len(channels_data))
    return channels_data


def get_recent_videos(
    playlist_id: str,
    quota: YouTubeQuotaContext,
    max_results: int = 15,
) -> list[dict]:
    """Fetch the most recent uploads from a channel's uploads playlist.

    Cost: 1 credit per call.
    """
    api_key, counter = quota.prepare_for_charge(PLAYLIST_CREDIT_COST)
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": max_results,
        "key": api_key,
    }
    try:
        res = requests.get(f"{BASE_URL}/playlistItems", params=params, timeout=15).json()
    except Exception as exc:
        logger.warning("playlistItems API request failed for %s: %s", playlist_id, exc)
        return []

    counter.add(PLAYLIST_CREDIT_COST)
    return res.get("items", [])


def get_video_stats(
    video_ids: list[str],
    quota: YouTubeQuotaContext,
) -> list[dict]:
    """Fetch statistics for a list of video IDs (up to 50).

    Cost: 1 credit per call.
    """
    if not video_ids:
        return []

    api_key, counter = quota.prepare_for_charge(VIDEO_CREDIT_COST)
    params = {
        "part": "statistics",
        "id": ",".join(video_ids[:50]),
        "key": api_key,
    }
    try:
        res = requests.get(f"{BASE_URL}/videos", params=params, timeout=15).json()
    except Exception as exc:
        logger.warning("videos API request failed: %s", exc)
        return []

    counter.add(VIDEO_CREDIT_COST)
    return res.get("items", [])
