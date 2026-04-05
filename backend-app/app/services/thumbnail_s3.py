"""Thumbnail uploads — uses deterministic S3 keys (see ``app.constants.s3_keys``)."""

from __future__ import annotations

from app.constants.s3_keys import thumbnail_s3_key
from app.services.s3_upload import upload_to_s3


def upload_thumbnail_png(job_id: str, image_bytes: bytes) -> str:
    """Upload PNG bytes for ``job_id``; same key on every attempt (retry-safe)."""
    return upload_to_s3(image_bytes, thumbnail_s3_key(job_id))
