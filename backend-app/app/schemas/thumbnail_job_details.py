"""MongoDB ``thumbnail_job_details`` document shape (collection: ``thumbnail_job_details``).

One document per thumbnail job (including each feedback iteration). ``job_id`` matches
the PostgreSQL ``thumbnail_jobs.id`` (stored as string).

Schema::

    {
        "job_id": str,               # PG thumbnail_jobs.id (UUID string)
        "reference_image_url": str,
        "base_image_urls": list[str],
        "reference_image_s3_key": str,   # optional; worker refreshes read URLs
        "base_image_s3_keys": list[str],
        "title": str,
        "include_title": bool,
        "creative_comments": str,    # merged on each iteration
        "model": str,
        "feedback": str | None,
        "prompt_used": str | None,
        "created_at": datetime,
    }

Indexes: unique on ``job_id`` (see ``mongo_repo.ensure_thumbnail_job_details_indexes``).
"""

from datetime import datetime
from typing import TypedDict


class ThumbnailJobDetailsPayload(TypedDict, total=False):
    """Body fields for ``mongo_repo.create_details`` (``job_id`` is passed separately)."""

    reference_image_url: str
    base_image_urls: list[str]
    reference_image_s3_key: str
    base_image_s3_keys: list[str]
    title: str
    include_title: bool
    creative_comments: str
    model: str
    feedback: str | None
    prompt_used: str | None
    created_at: datetime
