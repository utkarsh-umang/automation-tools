"""Repository for yt_daily_usage collection."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.mongo.read import fetch_from_collection
from app.mongo.update import update_document
from app.mongo.upsert import upsert_document

COLLECTION = "yt_daily_usage"
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def _today() -> str:
    return datetime.now(PACIFIC_TZ).date().isoformat()


def get_or_create_today() -> dict:
    """Return today's usage document, creating it if it doesn't exist."""
    today = _today()
    upsert_document(
        COLLECTION,
        query={"date": today},
        data={
            "$setOnInsert": {
                "date": today,
                "creditsUsed": 0,
                "creditsByKey": {},
                "creditLimit": 10000,
                "activeBatchId": None,
                "runsCompleted": 0,
            }
        },
    )
    result = fetch_from_collection(COLLECTION, {"date": today})
    if not result.success or not result.data:
        raise RuntimeError("Failed to get or create daily_usage document")
    return result.data[0]


def get_today() -> dict | None:
    """Fetch today's usage document or None if it doesn't exist."""
    today = _today()
    result = fetch_from_collection(COLLECTION, {"date": today})
    if not result.success or not result.data:
        return None
    return result.data[0]


def set_credits_used(value: int) -> None:
    """Overwrite creditsUsed for today."""
    update_document(
        COLLECTION,
        {"date": _today()},
        {"$set": {"creditsUsed": value}},
    )


def set_credits_used_and_by_key(total: int, credits_by_key: dict[str, int]) -> None:
    """Persist aggregate daily credits and per-key breakdown."""
    update_document(
        COLLECTION,
        {"date": _today()},
        {"$set": {"creditsUsed": total, "creditsByKey": credits_by_key}},
    )


def set_active_batch(batch_id: str) -> None:
    update_document(
        COLLECTION,
        {"date": _today()},
        {"$set": {"activeBatchId": batch_id}},
    )


def clear_active_batch() -> None:
    update_document(
        COLLECTION,
        {"date": _today()},
        {"$set": {"activeBatchId": None}},
    )


def increment_runs() -> None:
    update_document(
        COLLECTION,
        {"date": _today()},
        {"$inc": {"runsCompleted": 1}},
    )
