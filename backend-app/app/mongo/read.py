"""MongoDB read operations."""

from app.mongo.get_connection import get_database_connection
from app.mongo.helpers import convert_objectid_to_str
from app.schemas.common import StatusOr


def fetch_from_collection(
    collection: str,
    query: dict,
    db_name: str | None = None,
) -> StatusOr:
    """Fetch all documents matching query."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        cursor = coll.find(query)
        docs = list(cursor)
        converted = convert_objectid_to_str(docs)
        return StatusOr.ok(converted)
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))


def fetch_from_collection_with_options(
    collection: str,
    query: dict,
    sort: list[tuple[str, int]] | None = None,
    limit: int | None = None,
    skip: int = 0,
    projection: dict | None = None,
    db_name: str | None = None,
) -> StatusOr:
    """Fetch with pagination, sort, and field projection."""
    try:
        db = get_database_connection(db_name=db_name)
        coll = db[collection]
        cursor = coll.find(query, projection or {})
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)
        docs = list(cursor)
        converted = convert_objectid_to_str(docs)
        return StatusOr.ok(converted)
    except Exception as e:
        return StatusOr.error("DB_ERROR", str(e))
