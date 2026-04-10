"""MongoDB access for ``thumbnail_job_details``.

All reads/writes for this collection go through this module. Schema: see
``app.schemas.thumbnail_job_details``.
"""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.mongo.get_connection import get_database_connection
from app.schemas.thumbnail_job_details import ThumbnailJobDetailsPayload

THUMBNAIL_JOB_DETAILS_COLLECTION = "thumbnail_job_details"


def _collection(db_name: str | None = None) -> Collection:
    db = get_database_connection(db_name=db_name)
    return db[THUMBNAIL_JOB_DETAILS_COLLECTION]


def ensure_thumbnail_job_details_indexes(db_name: str | None = None) -> None:
    """Create unique index on ``job_id`` (idempotent)."""
    coll = _collection(db_name)
    coll.create_index(
        "job_id",
        unique=True,
        name="idx_thumbnail_job_details_job_id",
    )


def create_details(
    job_id: str,
    payload: ThumbnailJobDetailsPayload,
    *,
    db_name: str | None = None,
) -> None:
    doc: dict[str, Any] = {"job_id": job_id, **dict(payload)}
    _collection(db_name).insert_one(doc)


def get_details(job_id: str, *, db_name: str | None = None) -> dict[str, Any] | None:
    return _collection(db_name).find_one({"job_id": job_id})


def get_details_many(
    job_ids: list[str], *, db_name: str | None = None
) -> dict[str, dict[str, Any]]:
    """Return ``job_id`` → document for all matching jobs (empty map if ``job_ids`` empty)."""
    if not job_ids:
        return {}
    coll = _collection(db_name)
    out: dict[str, dict[str, Any]] = {}
    for doc in coll.find({"job_id": {"$in": job_ids}}):
        jid = doc.get("job_id")
        if jid is not None:
            out[str(jid)] = doc
    return out


def update_prompt_used(
    job_id: str, prompt_used: str, *, db_name: str | None = None
) -> None:
    _collection(db_name).update_one(
        {"job_id": job_id},
        {"$set": {"prompt_used": prompt_used}},
    )


__all__ = [
    "THUMBNAIL_JOB_DETAILS_COLLECTION",
    "create_details",
    "ensure_thumbnail_job_details_indexes",
    "get_details",
    "get_details_many",
    "update_prompt_used",
]
