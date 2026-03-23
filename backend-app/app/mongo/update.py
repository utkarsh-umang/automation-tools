"""MongoDB update operations (non-upsert)."""

from app.mongo.get_connection import get_database_connection
from app.schemas.common import StatusOr


def update_document(
    collection: str,
    query: dict,
    update: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Update a single document matching query. Use MongoDB operators like $set, $inc."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.update_one(query, update)
        return StatusOr.ok({"modified_count": result.modified_count})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))


def update_multiple_documents(
    collection: str,
    query: dict,
    update: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Update all documents matching query. Use MongoDB operators like $set, $inc."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.update_many(query, update)
        return StatusOr.ok({"modified_count": result.modified_count})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))


def count_documents(
    collection: str,
    query: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Count documents matching query."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        count = coll.count_documents(query)
        return StatusOr.ok({"count": count})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))
