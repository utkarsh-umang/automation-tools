"""MongoDB connection manager — singleton, sync/async, environment-aware."""

import threading
from typing import Any

from app.core.config import config


class MongoConnectionManager:
    """Singleton connection manager for MongoDB."""

    _instance: "MongoConnectionManager | None" = None
    _lock = threading.Lock()
    _connections: dict[tuple[str, bool], Any] = {}

    def __new__(cls) -> "MongoConnectionManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def _get_uri(self) -> str:
        if config.ENVIRONMENT == "local":
            return config.MONGO_LOCAL_URI
        if config.GCP_PROJECT_ID and config.GCP_SECRET_NAME:
            try:
                from google.cloud import secretmanager

                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{config.GCP_PROJECT_ID}/secrets/{config.GCP_SECRET_NAME}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("utf-8")
            except ImportError:
                pass
            except Exception:
                pass
        if config.MONGO_PROD_URI:
            return config.MONGO_PROD_URI
        return config.MONGO_LOCAL_URI

    def get_connection(
        self, db_name: str | None = None, is_test_write: bool = False
    ) -> Any:
        """Return cached or new database handle. Sync (PyMongo) for local, async (Motor) for prod."""
        db = db_name or (
            config.MONGO_TEST_DB_NAME if is_test_write else config.MONGO_DB_NAME
        )
        cache_key = (db, is_test_write)
        if cache_key in self._connections:
            return self._connections[cache_key]

        uri = self._get_uri()
        from pymongo import MongoClient

        client = MongoClient(uri)

        database = client[db]
        self._connections[cache_key] = database
        return database


_manager = MongoConnectionManager()


def get_mongo_manager() -> MongoConnectionManager:
    return _manager
