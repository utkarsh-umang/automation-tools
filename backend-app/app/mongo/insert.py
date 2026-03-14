"""MongoDB insert operations."""

from app.mongo.get_connection import get_database_connection
from app.schemas.common import StatusOr


def insert_document(
    collection: str,
    data: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Insert a single document. Returns StatusOr with inserted_id in data on success."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.insert_one(data)
        return StatusOr.ok({"inserted_id": str(result.inserted_id)})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))


def insert_multiple_documents(
    collection: str,
    data: list[dict],
    db_name: str | None = None,
) -> StatusOr:
    """Insert multiple documents. Returns StatusOr with inserted_ids in data on success."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.insert_many(data)
        return StatusOr.ok({"inserted_ids": [str(oid) for oid in result.inserted_ids]})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))
