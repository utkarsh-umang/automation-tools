"""Thumbnail API business logic (delegates to repos + ``thumbnail_access``)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import mongo_repo, pg_repo
from app.schemas.thumbnail_job_details import ThumbnailJobDetailsPayload
from app.schemas.thumbnails import (
    ThumbnailCreateRequest,
    ThumbnailFeedbackRequest,
    ThumbnailHistoryResponse,
    ThumbnailJobCreatedResponse,
    ThumbnailJobPublic,
    ThumbnailListResponse,
)
from app.services.thumbnail_access import require_thumbnail_job_owner


def _as_uuid(v: Any) -> uuid.UUID:
    return v if isinstance(v, uuid.UUID) else uuid.UUID(str(v))


def _job_row_to_public(job: dict[str, Any], mongo: dict[str, Any] | None) -> ThumbnailJobPublic:
    base = {
        "id": _as_uuid(job["id"]),
        "status": str(job["status"]),
        "iteration": int(job["iteration"]),
        "result_url": job.get("result_url"),
        "error": job.get("error"),
        "parent_job_id": _as_uuid(job["parent_job_id"]) if job.get("parent_job_id") else None,
        "root_job_id": _as_uuid(job["root_job_id"]) if job.get("root_job_id") else None,
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "completed_at": job.get("completed_at"),
        "reference_image_url": None,
        "base_image_urls": None,
        "title": None,
        "include_title": None,
        "creative_comments": None,
        "model": None,
        "feedback": None,
        "prompt_used": None,
    }
    if mongo:
        m = {k: v for k, v in mongo.items() if k not in ("_id", "job_id")}
        for k in (
            "reference_image_url",
            "base_image_urls",
            "title",
            "include_title",
            "creative_comments",
            "model",
            "feedback",
            "prompt_used",
        ):
            if k in m:
                base[k] = m[k]
    return ThumbnailJobPublic.model_validate(base)


async def create_thumbnail_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    body: ThumbnailCreateRequest,
) -> ThumbnailJobCreatedResponse:
    """``created_by`` is always ``user_id`` from the verified JWT."""
    job_id = uuid.uuid4()
    await pg_repo.create_job(
        session,
        job_id,
        user_id,
        parent_job_id=None,
        root_job_id=job_id,
        iteration=1,
    )
    payload: ThumbnailJobDetailsPayload = {
        "reference_image_url": body.reference_image_url,
        "base_image_urls": body.base_image_urls,
        "title": body.title,
        "include_title": body.include_title,
        "creative_comments": body.creative_comments,
        "model": body.model,
        "feedback": None,
        "prompt_used": None,
        "created_at": datetime.now(UTC),
    }
    mongo_repo.create_details(str(job_id), payload)
    from app.worker.thumbnail.generate import generate_thumbnail_task

    generate_thumbnail_task.delay(str(job_id))
    return ThumbnailJobCreatedResponse(id=job_id, status="pending")


async def list_thumbnail_jobs(
    session: AsyncSession,
    user_id: uuid.UUID,
    cursor: uuid.UUID | None,
    limit: int,
) -> ThumbnailListResponse:
    rows = await pg_repo.list_jobs_by_user(session, user_id, cursor, limit)
    jobs = [_job_row_to_public(r, None) for r in rows]
    next_cursor: uuid.UUID | None = None
    if rows and len(rows) == limit:
        next_cursor = _as_uuid(rows[-1]["id"])
    return ThumbnailListResponse(jobs=jobs, next_cursor=next_cursor)


async def get_thumbnail_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> ThumbnailJobPublic:
    job = await require_thumbnail_job_owner(session, job_id, user_id)
    mongo = mongo_repo.get_details(str(job_id))
    return _job_row_to_public(job, mongo)


async def submit_thumbnail_feedback(
    session: AsyncSession,
    user_id: uuid.UUID,
    parent_job_id: uuid.UUID,
    body: ThumbnailFeedbackRequest,
) -> ThumbnailJobCreatedResponse:
    parent = await require_thumbnail_job_owner(session, parent_job_id, user_id)
    details = mongo_repo.get_details(str(parent_job_id))
    if not details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stored details for parent job",
        )

    new_id = uuid.uuid4()
    root_raw = parent.get("root_job_id") or parent["id"]
    root_uuid = _as_uuid(root_raw)
    iteration = int(parent["iteration"]) + 1

    await pg_repo.create_job(
        session,
        new_id,
        user_id,
        parent_job_id=parent_job_id,
        root_job_id=root_uuid,
        iteration=iteration,
    )

    merged = (
        f"{details.get('creative_comments', '')}\n\n---\nFeedback: {body.feedback}"
    )
    payload: ThumbnailJobDetailsPayload = {
        "reference_image_url": str(details["reference_image_url"]),
        "base_image_urls": list(details.get("base_image_urls", [])),
        "title": str(details["title"]),
        "include_title": bool(details.get("include_title", True)),
        "creative_comments": merged,
        "model": body.model,
        "feedback": body.feedback,
        "prompt_used": None,
        "created_at": datetime.now(UTC),
    }
    mongo_repo.create_details(str(new_id), payload)

    from app.worker.thumbnail.generate import generate_thumbnail_task

    generate_thumbnail_task.delay(str(new_id))
    return ThumbnailJobCreatedResponse(id=new_id, status="pending")


async def get_thumbnail_history(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> ThumbnailHistoryResponse:
    job = await require_thumbnail_job_owner(session, job_id, user_id)
    root_raw = job.get("root_job_id") or job["id"]
    root_uuid = _as_uuid(root_raw)
    rows = await pg_repo.get_history(session, root_uuid)
    jobs = [
        _job_row_to_public(r, mongo_repo.get_details(str(r["id"]))) for r in rows
    ]
    return ThumbnailHistoryResponse(jobs=jobs)
