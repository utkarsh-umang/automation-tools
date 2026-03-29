"""Repository for yt_batches collection."""

from datetime import datetime

from bson import ObjectId

from app.mongo.delete import delete_document
from app.mongo.insert import insert_document
from app.mongo.read import fetch_from_collection, fetch_from_collection_with_options
from app.mongo.update import update_document
from app.schemas.youtube.batch import BatchDocument, BatchFilters, BatchStatus

COLLECTION = "yt_batches"


def create(
    name: str,
    keyword: str,
    filters: BatchFilters,
    total_terms: int,
) -> str:
    """Insert a new batch document. Returns the inserted _id as string."""
    doc = BatchDocument(
        name=name,
        keyword=keyword,
        filters=filters,
        totalTerms=total_terms,
        processedTerms=0,
        status=BatchStatus.QUEUED,
        createdAt=datetime.utcnow(),
    )
    data = doc.model_dump(exclude={"id"})
    result = insert_document(COLLECTION, data)
    if not result.success:
        raise RuntimeError(f"Failed to create batch: {result.message}")
    return result.data["inserted_id"]


def get_by_id(batch_id: str) -> dict | None:
    """Fetch a single batch document by _id. Returns dict or None."""
    result = fetch_from_collection(COLLECTION, {"_id": ObjectId(batch_id)})
    if not result.success or not result.data:
        return None
    return result.data[0]


def list_all() -> list[dict]:
    """Fetch all batches, newest first."""
    result = fetch_from_collection_with_options(
        COLLECTION,
        query={},
        sort=[("createdAt", -1)],
    )
    if not result.success:
        return []
    return result.data or []


def update_status(
    batch_id: str,
    status: BatchStatus,
    *,
    completed_at: datetime | None = None,
    last_triggered_at: datetime | None = None,
    clear_completed_at: bool = False,
) -> None:
    fields: dict = {"status": status.value}
    if completed_at is not None:
        fields["completedAt"] = completed_at
    if last_triggered_at is not None:
        fields["lastTriggeredAt"] = last_triggered_at
    update: dict = {"$set": fields}
    if clear_completed_at:
        update["$unset"] = {"completedAt": ""}
    update_document(COLLECTION, {"_id": ObjectId(batch_id)}, update)


def increment_processed_terms(batch_id: str) -> None:
    update_document(
        COLLECTION,
        {"_id": ObjectId(batch_id)},
        {"$inc": {"processedTerms": 1}},
    )


def decrement_processed_terms(batch_id: str, n: int = 1) -> None:
    """Decrease processedTerms by n without going below zero."""
    if n <= 0:
        return
    update_document(
        COLLECTION,
        {"_id": ObjectId(batch_id), "processedTerms": {"$gte": n}},
        {"$inc": {"processedTerms": -n}},
    )


def delete(batch_id: str) -> None:
    """Hard-delete a batch document."""
    delete_document(COLLECTION, {"_id": ObjectId(batch_id)})
