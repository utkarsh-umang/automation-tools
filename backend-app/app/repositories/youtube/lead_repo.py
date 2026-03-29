"""Repository for yt_leads collection."""

from bson import ObjectId

from app.mongo.delete import delete_multiple_documents
from app.mongo.get_connection import get_database_connection
from app.mongo.insert import insert_multiple_documents
from app.mongo.read import fetch_from_collection_with_options
from app.mongo.update import count_documents

COLLECTION = "yt_leads"


def insert_many(leads: list[dict]) -> None:
    """Bulk-insert lead documents. Raises on failure."""
    if not leads:
        return
    result = insert_multiple_documents(COLLECTION, leads)
    if not result.success:
        raise RuntimeError(f"Failed to insert leads: {result.message}")


def paginated_list(
    batch_id: str,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict], int]:
    """Return (leads, total) sorted by score descending."""
    skip = (page - 1) * page_size
    query = {"batchId": batch_id}

    count_result = count_documents(COLLECTION, query)
    total = count_result.data["count"] if count_result.success else 0

    result = fetch_from_collection_with_options(
        COLLECTION,
        query=query,
        sort=[("score", -1)],
        skip=skip,
        limit=page_size,
    )
    leads = result.data if result.success else []
    return leads, total


def get_all_for_batch(batch_id: str) -> list[dict]:
    """Return all leads for a batch sorted by score descending (no pagination)."""
    result = fetch_from_collection_with_options(
        COLLECTION,
        query={"batchId": batch_id},
        sort=[("score", -1)],
        skip=0,
        limit=None,
    )
    return result.data if result.success else []


def deduplicate_for_batch(batch_id: str) -> int:
    """Remove duplicate channels for a batch, keeping the one with the highest score.

    Returns the number of duplicates removed.
    """
    db = get_database_connection()
    coll = db[COLLECTION]

    # Aggregate: group by channelId, collect all doc _ids and max score's _id
    pipeline = [
        {"$match": {"batchId": batch_id}},
        {"$sort": {"score": -1}},
        {
            "$group": {
                "_id": "$channelId",
                "bestId": {"$first": "$_id"},
                "allIds": {"$push": "$_id"},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    duplicates = list(coll.aggregate(pipeline))

    ids_to_delete = []
    for group in duplicates:
        for doc_id in group["allIds"]:
            if doc_id != group["bestId"]:
                ids_to_delete.append(doc_id)

    if ids_to_delete:
        coll.delete_many({"_id": {"$in": ids_to_delete}})

    return len(ids_to_delete)


def delete_for_batch(batch_id: str) -> None:
    delete_multiple_documents(COLLECTION, {"batchId": batch_id})


def delete_for_batch_term(batch_id: str, term_id: str) -> int:
    """Delete leads for one search term. Returns deleted count."""
    query = {
        "batchId": batch_id,
        "$or": [
            {"searchTermId": term_id},
            {"searchTermId": ObjectId(term_id)},
        ],
    }
    result = delete_multiple_documents(COLLECTION, query)
    if not result.success:
        return 0
    return int(result.data.get("deleted_count", 0))
