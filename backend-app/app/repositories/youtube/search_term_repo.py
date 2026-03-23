"""Repository for yt_search_terms collection."""

from datetime import datetime

from bson import ObjectId

from app.mongo.delete import delete_multiple_documents
from app.mongo.insert import insert_multiple_documents
from app.mongo.read import fetch_from_collection, fetch_from_collection_with_options
from app.mongo.update import update_document
from app.schemas.youtube.search_term import SearchTermDocument, TermStatus

COLLECTION = "yt_search_terms"


def create_many(batch_id: str, terms: list[str]) -> list[str]:
    """Insert one SearchTerm document per term. Returns inserted IDs."""
    docs = [
        SearchTermDocument(
            batchId=batch_id,
            term=term,
            position=idx,
            status=TermStatus.PENDING,
        ).model_dump(exclude={"id"})
        for idx, term in enumerate(terms)
    ]
    result = insert_multiple_documents(COLLECTION, docs)
    if not result.success:
        raise RuntimeError(f"Failed to create search terms: {result.message}")
    return result.data["inserted_ids"]


def get_pending_for_batch(batch_id: str) -> list[dict]:
    """Fetch pending terms for a batch, ordered by position."""
    result = fetch_from_collection_with_options(
        COLLECTION,
        query={"batchId": batch_id, "status": TermStatus.PENDING.value},
        sort=[("position", 1)],
    )
    if not result.success:
        return []
    return result.data or []


def get_all_for_batch(batch_id: str) -> list[dict]:
    """Fetch all terms for a batch, ordered by position."""
    result = fetch_from_collection_with_options(
        COLLECTION,
        query={"batchId": batch_id},
        sort=[("position", 1)],
    )
    if not result.success:
        return []
    return result.data or []


def get_by_id(term_id: str) -> dict | None:
    result = fetch_from_collection(COLLECTION, {"_id": ObjectId(term_id)})
    if not result.success or not result.data:
        return None
    return result.data[0]


def update_status(term_id: str, status: TermStatus) -> None:
    update_document(
        COLLECTION,
        {"_id": ObjectId(term_id)},
        {"$set": {"status": status.value}},
    )


def mark_running(term_id: str) -> None:
    update_document(
        COLLECTION,
        {"_id": ObjectId(term_id)},
        {"$set": {"status": TermStatus.RUNNING.value, "startedAt": datetime.utcnow()}},
    )


def mark_done(
    term_id: str,
    credits_used: int,
    channels_discovered: int,
    channels_qualified: int,
    emails_found: int,
) -> None:
    update_document(
        COLLECTION,
        {"_id": ObjectId(term_id)},
        {
            "$set": {
                "status": TermStatus.DONE.value,
                "creditsUsed": credits_used,
                "channelsDiscovered": channels_discovered,
                "channelsQualified": channels_qualified,
                "emailsFound": emails_found,
                "completedAt": datetime.utcnow(),
            }
        },
    )


def mark_failed(term_id: str, error_message: str) -> None:
    update_document(
        COLLECTION,
        {"_id": ObjectId(term_id)},
        {
            "$set": {
                "status": TermStatus.FAILED.value,
                "errorMessage": error_message,
                "completedAt": datetime.utcnow(),
            }
        },
    )


def reset_to_pending(term_id: str) -> None:
    """Roll back a term to pending (credit limit mid-run)."""
    update_document(
        COLLECTION,
        {"_id": ObjectId(term_id)},
        {
            "$set": {
                "status": TermStatus.PENDING.value,
                "startedAt": None,
                "errorMessage": None,
            }
        },
    )


def delete_for_batch(batch_id: str) -> None:
    delete_multiple_documents(COLLECTION, {"batchId": batch_id})
