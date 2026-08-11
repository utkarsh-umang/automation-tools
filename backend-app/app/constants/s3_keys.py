"""S3 object key conventions (EP-05 / SBL-18).

Generated thumbnails use a **deterministic** key per ``job_id`` so Celery retries
overwrite the same object (idempotent uploads). No timestamps or random
suffixes.

Format::

    thumbnails/{job_id}.png

User-provided inputs (multipart uploads)::

    thumbnail-inputs/{job_id}/reference{ext}
    thumbnail-inputs/{job_id}/base/{index}{ext}

Short-video clips follow the same determinism, with a folder level so a client's
work groups together (mirroring Studio's media keys)::

    short-video/{folder_id}/{job_id}/clips/{index}.mp4
    short-video-inputs/{job_id}/source{ext}

``job_id`` is the PostgreSQL / API UUID string (e.g. ``8b3e...``).
"""

from __future__ import annotations

from pathlib import Path

THUMBNAIL_S3_KEY_PREFIX = "thumbnails"
THUMBNAIL_INPUTS_PREFIX = "thumbnail-inputs"

SHORT_VIDEO_PREFIX = "short-video"
SHORT_VIDEO_INPUTS_PREFIX = "short-video-inputs"

_CONTENT_TYPE_TO_EXT: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def input_image_extension(filename: str | None, content_type: str | None) -> str:
    """Pick ``.png`` / ``.jpg`` / … from filename suffix, else ``Content-Type``, else ``.bin``."""
    if filename:
        ext = Path(filename).suffix.lower()
        if ext == ".jpeg":
            ext = ".jpg"
        if ext in {".png", ".jpg", ".webp", ".gif"}:
            return ext
    ct = (content_type or "").split(";")[0].strip().lower()
    return _CONTENT_TYPE_TO_EXT.get(ct, ".bin")


def thumbnail_input_reference_key(
    job_id: str,
    filename: str | None,
    content_type: str | None,
) -> str:
    ext = input_image_extension(filename, content_type)
    return f"{THUMBNAIL_INPUTS_PREFIX}/{job_id}/reference{ext}"


def thumbnail_input_base_key(
    job_id: str,
    index: int,
    filename: str | None,
    content_type: str | None,
) -> str:
    ext = input_image_extension(filename, content_type)
    return f"{THUMBNAIL_INPUTS_PREFIX}/{job_id}/base/{index}{ext}"


def thumbnail_s3_key(job_id: str) -> str:
    """Return the S3 object key for a thumbnail job (``thumbnails/{job_id}.png``)."""
    return f"{THUMBNAIL_S3_KEY_PREFIX}/{job_id}.png"


def thumbnail_s3_candidate_key(job_id: str, index: int) -> str:
    """S3 key for one of a job's generated candidates (``thumbnails/{job_id}/candidate-{index}.png``).

    Deterministic per ``(job_id, index)`` so Celery retries overwrite the same
    object, same idempotency guarantee as ``thumbnail_s3_key``.
    """
    return f"{THUMBNAIL_S3_KEY_PREFIX}/{job_id}/candidate-{index}.png"


def short_video_clip_key(folder_id: str, job_id: str, index: int) -> str:
    """S3 key for one produced clip (``short-video/{folder}/{job}/clips/{i}.mp4``).

    Deterministic per ``(folder_id, job_id, index)``, same idempotency guarantee
    as ``thumbnail_s3_candidate_key``: a Celery retry overwrites its own object
    instead of orphaning the first attempt.
    """
    return f"{SHORT_VIDEO_PREFIX}/{folder_id}/{job_id}/clips/{index}.mp4"


def short_video_source_key(job_id: str, suffix: str = ".mp4") -> str:
    """S3 key for the downloaded source (``short-video-inputs/{job}/source{ext}``).

    Its own prefix so a bucket lifecycle rule can expire sources (~7 days)
    without touching the clips, which persist. Sources are two orders of
    magnitude larger than thumbnails, so leaving them around is the expensive
    mistake.
    """
    return f"{SHORT_VIDEO_INPUTS_PREFIX}/{job_id}/source{suffix}"
