"""MongoDB delete operations."""

from app.mongo.get_connection import get_database_connection
from app.schemas.common import StatusOr


def delete_document(
    collection: str,
    query: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Delete a single document matching query."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.delete_one(query)
        return StatusOr.ok({"deleted_count": result.deleted_count})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))


def delete_multiple_documents(
    collection: str,
    query: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Delete all documents matching query."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.delete_many(query)
        return StatusOr.ok({"deleted_count": result.deleted_count})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))


def archive_document(
    collection: str,
    query: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Soft delete: set status='archived' on matching document."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.update_one(query, {"$set": {"status": "archived"}})
        return StatusOr.ok({"modified_count": result.modified_count})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))


def archive_multiple_documents(
    collection: str,
    query: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Soft delete: set status='archived' on all matching documents."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.update_many(query, {"$set": {"status": "archived"}})
        return StatusOr.ok({"modified_count": result.modified_count})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))
