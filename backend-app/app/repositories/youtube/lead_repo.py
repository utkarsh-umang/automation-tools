"""Repository for yt_leads collection."""

from app.mongo.delete import delete_multiple_documents
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


def delete_for_batch(batch_id: str) -> None:
    delete_multiple_documents(COLLECTION, {"batchId": batch_id})
