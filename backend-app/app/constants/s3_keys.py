"""S3 object key conventions (EP-05 / SBL-18).

Generated thumbnails use a **deterministic** key per ``job_id`` so Celery retries
overwrite the same object (idempotent uploads). No timestamps or random
suffixes.

Format::

    thumbnails/{job_id}.png

``job_id`` is the PostgreSQL / API UUID string (e.g. ``8b3e...``).
"""

from __future__ import annotations

THUMBNAIL_S3_KEY_PREFIX = "thumbnails"


def thumbnail_s3_key(job_id: str) -> str:
    """Return the S3 object key for a thumbnail job (``thumbnails/{job_id}.png``)."""
    return f"{THUMBNAIL_S3_KEY_PREFIX}/{job_id}.png"
