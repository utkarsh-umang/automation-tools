"""Get MongoDB database connection."""

from typing import Any

from app.mongo.connection_manager import get_mongo_manager


def get_database_connection(
    db_name: str | None = None,
    is_test_write: bool = False,
) -> Any:
    """
    Return a MongoDB database handle.

    Defaults db_name to config.MONGO_DB_NAME (or MONGO_TEST_DB_NAME when is_test_write).
    Returns PyMongo Database for local, Motor AsyncIOMotorDatabase for prod.
    """
    manager = get_mongo_manager()
    return manager.get_connection(db_name=db_name, is_test_write=is_test_write)
