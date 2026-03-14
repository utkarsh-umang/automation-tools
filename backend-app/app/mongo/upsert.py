"""MongoDB upsert operations."""

from app.mongo.get_connection import get_database_connection
from app.schemas.common import StatusOr


def upsert_document(
    collection: str,
    query: dict,
    data: dict,
    db_name: str | None = None,
) -> StatusOr:
    """
    Upsert a document. Uses update_one(..., upsert=True).
    Supports $set and $unset operators in data.
    """
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        result = coll.update_one(query, data, upsert=True)
        if result.upserted_id:
            return StatusOr.ok({"upserted_id": str(result.upserted_id)})
        return StatusOr.ok({"modified_count": result.modified_count})
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))
