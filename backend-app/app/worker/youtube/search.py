"""YouTube channel ID collection via the Search API.

Ported from youtube_script.py — collect_channel_ids().
Global variables replaced with explicit parameters; credit tracking
injected via YouTubeQuotaContext.
"""

import logging
import time

import requests

from app.worker.youtube.quota_context import YouTubeQuotaContext

logger = logging.getLogger(__name__)

SEARCH_ORDERS = ["relevance"]
MAX_SEARCH_PAGES = 60
LOW_YIELD_PAGES_TO_STOP = 3
MIN_NEW_CHANNELS_PER_PAGE = 5
TARGET_CHANNEL_POOL = 500
SEARCH_CREDIT_COST = 100
BASE_URL = "https://www.googleapis.com/youtube/v3"


def collect_channel_ids(
    keyword: str,
    quota: YouTubeQuotaContext,
    region: str = "US",
    relevance_language: str = "en",
) -> list[str]:
    """Search YouTube for channels matching keyword across 3 sort orders.

    Stops early on low yield or when TARGET_CHANNEL_POOL is reached.
    Raises CreditLimitExceeded if the daily quota is hit on the last key mid-search.

    Returns a list of unique channel IDs.
    """
    all_channel_ids: set[str] = set()
    low_yield_pages = 0

    for order in SEARCH_ORDERS:
        logger.info("collect_channel_ids: order=%s keyword=%r", order, keyword)
        next_page_token = None

        pages_per_order = MAX_SEARCH_PAGES // len(SEARCH_ORDERS)

        for page in range(pages_per_order):
            api_key, counter = quota.prepare_for_charge(SEARCH_CREDIT_COST)

            params: dict = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": order,
                "maxResults": 50,
                "relevanceLanguage": relevance_language,
                "regionCode": region,
                "key": api_key,
            }
            if next_page_token:
                params["pageToken"] = next_page_token

            try:
                res = requests.get(f"{BASE_URL}/search", params=params, timeout=15).json()
            except Exception as exc:
                logger.warning("Search API request failed: %s", exc)
                break

            # Count credits after the call
            counter.add(SEARCH_CREDIT_COST)

            channel_ids = list(
                {item["snippet"]["channelId"] for item in res.get("items", [])}
            )
            prev_count = len(all_channel_ids)
            all_channel_ids.update(channel_ids)
            new_added = len(all_channel_ids) - prev_count

            logger.debug("page=%d order=%s +%d new channels", page + 1, order, new_added)

            if new_added < MIN_NEW_CHANNELS_PER_PAGE:
                low_yield_pages += 1
            else:
                low_yield_pages = 0

            if low_yield_pages >= LOW_YIELD_PAGES_TO_STOP:
                logger.info("Stopping early: low discovery yield after %d pages", page + 1)
                break

            if len(all_channel_ids) >= TARGET_CHANNEL_POOL:
                logger.info("Target channel pool of %d reached", TARGET_CHANNEL_POOL)
                break

            next_page_token = res.get("nextPageToken")
            if not next_page_token:
                break

            time.sleep(0.2)

        if len(all_channel_ids) >= TARGET_CHANNEL_POOL:
            break

    logger.info(
        "collect_channel_ids done: %d unique channels for keyword=%r",
        len(all_channel_ids),
        keyword,
    )
    return list(all_channel_ids)
