#!/usr/bin/env python3
"""One-off: repair thumbnail jobs whose reference was stored as ``reference.bin``.

Before the normalisation fix, an upload we could not name by extension landed as
``reference.bin`` with ``Content-Type: application/octet-stream``, which both
OpenAI and Gemini reject. Three jobs failed this way on 2026-08-19 (an AVIF
reference dragged through the ``image/*`` file picker).

The code fix only covers *new* uploads: the generate task reads
``reference_image_s3_key`` straight out of Mongo, so an affected job replays
against the same unreadable object no matter how many times it is retried. This
script repairs the stored input, then re-enqueues:

1. fetch the stored ``reference.bin``
2. transcode it via ``normalise_input_image`` — the same code path new uploads use
3. PUT it under the correct extension and Content-Type (the old object is left in
   place; it is small, and it is the evidence of what happened)
4. point Mongo's ``reference_image_s3_key`` / ``reference_image_url`` at it
5. clear the Postgres error and re-enqueue the Celery task

Run it **after** the fix is deployed — it imports ``app.services.image_normalise``
and needs Pillow, both of which arrive with that deploy. From inside the backend
container::

    docker exec -it automation-tools-backend-1 \\
        python scripts/repair_octet_stream_references.py            # dry run
    docker exec -it automation-tools-backend-1 \\
        python scripts/repair_octet_stream_references.py --commit   # do it

Idempotent: a job already pointing at a readable reference is skipped, so a
re-run after a partial failure resumes rather than duplicating work.

``--commit`` re-runs paid generations (gptimage / nanobanana are the capped
models), so it bills real API spend. Check ``/api/v1/thumbnails/usage`` first.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import boto3

from app.constants.s3_keys import content_type_for_key, thumbnail_input_reference_key
from app.core.config import config
from app.repositories import mongo_repo
from app.services.image_normalise import UnsupportedImageError, normalise_input_image

# The jobs that failed with the provider's octet-stream 400 on 2026-08-19.
AFFECTED_JOB_IDS = (
    "eabc218b-d237-4d2d-a051-33a0fa68c9f7",
    "0fe2d481-75f6-4919-8685-d6586c9363e7",
    "609cf538-dc97-4ca8-8af4-9cef82348bac",
)


def _direct_url(key: str) -> str:
    host = f"{config.THUMBNAIL_S3_BUCKET}.s3.{config.AWS_REGION}.amazonaws.com"
    return f"https://{host}/{key}"


def _repair_one(s3, job_id: str, *, commit: bool) -> bool:
    """Return True if this job was repaired (or would be, in a dry run)."""
    details = mongo_repo.get_details(job_id)
    if not details:
        print(f"  {job_id}: SKIP — no Mongo details")
        return False

    old_key = str(details.get("reference_image_s3_key") or "")
    if not old_key:
        print(f"  {job_id}: SKIP — no reference_image_s3_key")
        return False
    if content_type_for_key(old_key).startswith("image/"):
        print(f"  {job_id}: SKIP — reference already readable ({old_key})")
        return False

    raw = s3.get_object(Bucket=config.THUMBNAIL_S3_BUCKET, Key=old_key)["Body"].read()
    try:
        image = normalise_input_image(raw, Path(old_key).name, "application/octet-stream")
    except UnsupportedImageError as exc:
        print(f"  {job_id}: FAIL — stored reference is not decodable: {exc}")
        return False

    new_key = thumbnail_input_reference_key(job_id, image.ext)
    new_ct = content_type_for_key(new_key)
    print(
        f"  {job_id}: {old_key} (application/octet-stream, {len(raw)}B)"
        f" -> {new_key} ({new_ct}, {len(image.data)}B)"
    )
    if not commit:
        return True

    s3.put_object(
        Bucket=config.THUMBNAIL_S3_BUCKET,
        Key=new_key,
        Body=image.data,
        ContentType=new_ct,
    )
    head = s3.head_object(Bucket=config.THUMBNAIL_S3_BUCKET, Key=new_key)
    if head["ContentType"] != new_ct:
        raise RuntimeError(f"{new_key} stored as {head['ContentType']}, expected {new_ct}")

    mongo_repo._collection().update_one(
        {"job_id": job_id},
        {"$set": {
            "reference_image_s3_key": new_key,
            "reference_image_url": _direct_url(new_key),
        }},
    )
    print(f"    stored + Mongo updated (verified {head['ContentType']})")
    return True


def _requeue(job_ids: list[str]) -> None:
    """Clear the recorded error and re-enqueue. The task itself sets ``processing``."""
    import asyncio

    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal
    from app.worker.thumbnail.generate import generate_thumbnail_task

    async def _clear() -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text(
                    "UPDATE thumbnail_jobs SET status = 'pending', error = NULL,"
                    " updated_at = now() WHERE id = ANY(:ids)"
                ),
                {"ids": [uuid.UUID(j) for j in job_ids]},
            )
            await session.commit()

    asyncio.run(_clear())
    for job_id in job_ids:
        generate_thumbnail_task.delay(job_id)
        print(f"  re-enqueued {job_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="actually write to S3/Mongo/Postgres and re-enqueue (bills paid generations)",
    )
    args = parser.parse_args()

    if not config.THUMBNAIL_S3_BUCKET:
        raise SystemExit("THUMBNAIL_S3_BUCKET is not configured")

    mode = "COMMIT" if args.commit else "DRY RUN (pass --commit to apply)"
    print(f"Repairing {len(AFFECTED_JOB_IDS)} job(s) — {mode}\n")

    s3 = boto3.client("s3", region_name=config.AWS_REGION)
    repaired = [j for j in AFFECTED_JOB_IDS if _repair_one(s3, j, commit=args.commit)]

    if not repaired:
        print("\nNothing to do.")
        return
    if not args.commit:
        print(f"\n{len(repaired)} job(s) would be repaired and re-enqueued.")
        return

    print(f"\nRe-enqueueing {len(repaired)} job(s):")
    _requeue(repaired)
    print("\nDone. Watch: docker logs -f automation-tools-celery-worker-1")


if __name__ == "__main__":
    main()
