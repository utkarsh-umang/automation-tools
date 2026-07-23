"""Thumbnail API business logic (delegates to repos + ``thumbnail_access``)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.s3_keys import thumbnail_input_base_key, thumbnail_input_reference_key
from app.repositories import folder_repo, mongo_repo, pg_repo
from app.schemas.folders import FolderSummary, FolderSummaryResponse
from app.schemas.thumbnail_job_details import ThumbnailJobDetailsPayload
from app.schemas.thumbnails import (
    ModelUsage,
    ThumbnailFeedbackRequest,
    ThumbnailHistoryResponse,
    ThumbnailJobCreatedResponse,
    ThumbnailJobPublic,
    ThumbnailListResponse,
    ThumbnailUsageResponse,
)
from app.services import user_service
from app.services.s3_upload import S3UploadError, upload_to_s3
from app.services.thumbnail_access import require_thumbnail_job_owner

# Shared org-wide monthly allowance for the paid-per-image models — Flux Kontext
# (not in this set) is the cheap default and stays uncapped. Resets on the
# calendar month boundary (UTC).
CAPPED_MODELS = ("gptimage", "nanobanana")
MONTHLY_MODEL_CAP = 50


def _as_uuid(v: Any) -> uuid.UUID:
    return v if isinstance(v, uuid.UUID) else uuid.UUID(str(v))


def _start_of_current_month() -> datetime:
    now = datetime.now(UTC)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def _check_model_quota(model: str) -> None:
    if model not in CAPPED_MODELS:
        return
    used = mongo_repo.count_by_model_since(model, _start_of_current_month())
    if used >= MONTHLY_MODEL_CAP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Monthly limit of {MONTHLY_MODEL_CAP} {model} generations reached "
                "for the whole team. Try Flux Kontext instead, or wait until next month."
            ),
        )


def _job_row_to_public(
    job: dict[str, Any],
    mongo: dict[str, Any] | None,
    *,
    created_by_email: str | None = None,
) -> ThumbnailJobPublic:
    base = {
        "id": _as_uuid(job["id"]),
        "status": str(job["status"]),
        "iteration": int(job["iteration"]),
        "result_url": job.get("result_url"),
        "error": job.get("error"),
        "parent_job_id": _as_uuid(job["parent_job_id"]) if job.get("parent_job_id") else None,
        "root_job_id": _as_uuid(job["root_job_id"]) if job.get("root_job_id") else None,
        "created_by": _as_uuid(job["created_by"]),
        "created_by_email": created_by_email,
        "folder_id": _as_uuid(job["folder_id"]) if job.get("folder_id") else None,
        "candidate_urls": job.get("candidate_urls"),
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "completed_at": job.get("completed_at"),
        "reference_image_url": None,
        "base_image_urls": None,
        "title": None,
        "include_title": None,
        "creative_comments": None,
        "model": None,
        "shorts_or_reels": None,
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
            "shorts_or_reels",
            "feedback",
            "prompt_used",
        ):
            if k in m:
                base[k] = m[k]
    return ThumbnailJobPublic.model_validate(base)


async def create_thumbnail_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    reference: tuple[bytes, str | None, str | None],
    base_images: list[tuple[bytes, str | None, str | None]],
    title: str,
    include_title: bool,
    creative_comments: str,
    model: str,
    folder_id: uuid.UUID | None = None,
    shorts_or_reels: bool = False,
) -> ThumbnailJobCreatedResponse:
    """``created_by`` is always ``user_id`` from the verified JWT.

    ``folder_id`` (optional) pulls in that folder's persistent client-style
    prompt, prepended to ``creative_comments`` before generation. ``shorts_or_reels``
    generates a 9:16 vertical frame (Shorts/Reels) instead of 16:9 landscape.
    """
    if model not in ("gptimage", "nanobanana", "fluxkontext"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="model must be gptimage, nanobanana, or fluxkontext",
        )
    await _check_model_quota(model)

    if folder_id is not None:
        folder = await folder_repo.get_folder(session, folder_id)
        if folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found",
            )
        style_prompt = str(folder.get("style_prompt") or "").strip()
        if style_prompt:
            creative_comments = (
                f"CLIENT STYLE (always apply): {style_prompt}\n\n{creative_comments}"
                if creative_comments
                else f"CLIENT STYLE (always apply): {style_prompt}"
            )

    job_id = uuid.uuid4()
    jid_str = str(job_id)
    ref_bytes, ref_fn, ref_ct = reference

    await pg_repo.create_job(
        session,
        job_id,
        user_id,
        parent_job_id=None,
        root_job_id=job_id,
        iteration=1,
        folder_id=folder_id,
    )

    ref_key = thumbnail_input_reference_key(jid_str, ref_fn, ref_ct)
    try:
        ref_url = upload_to_s3(ref_bytes, ref_key)
        base_urls: list[str] = []
        base_keys: list[str] = []
        for i, (bdata, bfn, bct) in enumerate(base_images):
            bk = thumbnail_input_base_key(jid_str, i, bfn, bct)
            base_urls.append(upload_to_s3(bdata, bk))
            base_keys.append(bk)
    except S3UploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    payload: ThumbnailJobDetailsPayload = {
        "reference_image_url": ref_url,
        "base_image_urls": base_urls,
        "reference_image_s3_key": ref_key,
        "base_image_s3_keys": base_keys,
        "title": title,
        "include_title": include_title,
        "creative_comments": creative_comments,
        "model": model,
        "shorts_or_reels": shorts_or_reels,
        "feedback": None,
        "prompt_used": None,
        "created_at": datetime.now(UTC),
    }
    mongo_repo.create_details(jid_str, payload)
    from app.worker.thumbnail.generate import generate_thumbnail_task

    generate_thumbnail_task.delay(jid_str)
    return ThumbnailJobCreatedResponse(id=job_id, status="pending")


async def list_thumbnail_jobs(
    session: AsyncSession,
    user_id: uuid.UUID,
    cursor: uuid.UUID | None,
    limit: int,
    *,
    is_admin: bool = False,
    folder_id: uuid.UUID | None = None,
    roots_only: bool = False,
    include_unfoldered: bool = False,
) -> ThumbnailListResponse:
    """``is_admin`` lists thumbnail jobs across all members, not just ``user_id``.

    ``roots_only`` collapses each iteration chain to its latest version (one card
    per thumbnail); ``include_unfoldered`` also pulls in unfiled thumbnails, used
    for the Testing folder.
    """
    filter_user_id = None if is_admin else user_id
    rows = await pg_repo.list_jobs_by_user(
        session,
        filter_user_id,
        cursor,
        limit,
        folder_id=folder_id,
        roots_only=roots_only,
        include_unfoldered=include_unfoldered,
    )
    job_ids = [str(r["id"]) for r in rows]
    mongo_by_id = mongo_repo.get_details_many(job_ids)
    emails_by_id = await _creator_emails(session, rows) if is_admin else {}
    jobs = [
        _job_row_to_public(
            r,
            mongo_by_id.get(str(r["id"])),
            created_by_email=emails_by_id.get(_as_uuid(r["created_by"])),
        )
        for r in rows
    ]
    next_cursor: uuid.UUID | None = None
    if rows and len(rows) == limit:
        next_cursor = _as_uuid(rows[-1]["id"])
    return ThumbnailListResponse(jobs=jobs, next_cursor=next_cursor)


async def get_folder_summaries(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    is_admin: bool = False,
) -> FolderSummaryResponse:
    """Lineage count + cover image per folder for the album grid.

    Respects the same visibility rule as the list: ADMIN sees every member's
    thumbnails, MEMBER only their own.
    """
    filter_user_id = None if is_admin else user_id
    rows = await pg_repo.folder_lineage_summaries(session, filter_user_id)
    return FolderSummaryResponse(
        summaries=[
            FolderSummary(
                folder_id=r["folder_id"],
                count=r["count"],
                cover_url=r["cover_url"],
            )
            for r in rows
        ]
    )


async def _creator_emails(
    session: AsyncSession, rows: list[dict[str, Any]]
) -> dict[uuid.UUID, str]:
    creator_ids = {_as_uuid(r["created_by"]) for r in rows}
    users_by_id = await user_service.get_users_by_ids(session, list(creator_ids))
    return {uid: user.email for uid, user in users_by_id.items()}


async def get_thumbnail_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    *,
    is_admin: bool = False,
) -> ThumbnailJobPublic:
    job = await require_thumbnail_job_owner(session, job_id, user_id, is_admin=is_admin)
    mongo = mongo_repo.get_details(str(job_id))
    email = None
    if is_admin:
        emails = await _creator_emails(session, [job])
        email = emails.get(_as_uuid(job["created_by"]))
    return _job_row_to_public(job, mongo, created_by_email=email)


async def select_thumbnail_candidate(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    selected_url: str,
) -> ThumbnailJobPublic:
    """Owner picks one of the generated candidates; that becomes ``result_url``."""
    job = await require_thumbnail_job_owner(session, job_id, user_id)
    candidates = job.get("candidate_urls") or []
    if job.get("status") != "awaiting_selection" or selected_url not in candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not awaiting selection, or selected_url is not one of its candidates",
        )
    await pg_repo.update_completed(session, job_id, selected_url)
    updated = await pg_repo.get_job(session, job_id)
    mongo = mongo_repo.get_details(str(job_id))
    return _job_row_to_public(updated, mongo)


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
    await _check_model_quota(body.model)

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
        folder_id=parent.get("folder_id"),
    )

    # Base every iteration's prompt on the ROOT job's original creative direction
    # plus only the newest feedback — not the parent's, which may already carry
    # earlier rounds' feedback stacked on top of each other. Stacking raw feedback
    # across iterations feeds the model a growing, sometimes-contradictory
    # transcript instead of a clean current instruction.
    root_details = (
        details
        if str(root_uuid) == str(parent_job_id)
        else (mongo_repo.get_details(str(root_uuid)) or details)
    )
    merged = (
        f"{root_details.get('creative_comments', '')}\n\n"
        f"Latest revision request: {body.feedback}"
    )
    payload: ThumbnailJobDetailsPayload = {
        "reference_image_url": str(details["reference_image_url"]),
        "base_image_urls": list(details.get("base_image_urls", [])),
        "title": str(details["title"]),
        "include_title": bool(details.get("include_title", True)),
        "creative_comments": merged,
        "model": body.model,
        "shorts_or_reels": bool(details.get("shorts_or_reels", False)),
        "feedback": body.feedback,
        "prompt_used": None,
        "created_at": datetime.now(UTC),
    }
    rk = details.get("reference_image_s3_key")
    if rk:
        payload["reference_image_s3_key"] = str(rk)
    bk = details.get("base_image_s3_keys")
    if bk is not None:
        payload["base_image_s3_keys"] = list(bk)

    mongo_repo.create_details(str(new_id), payload)

    from app.worker.thumbnail.generate import generate_thumbnail_task

    generate_thumbnail_task.delay(str(new_id))
    return ThumbnailJobCreatedResponse(id=new_id, status="pending")


async def get_thumbnail_history(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    *,
    is_admin: bool = False,
) -> ThumbnailHistoryResponse:
    job = await require_thumbnail_job_owner(session, job_id, user_id, is_admin=is_admin)
    root_raw = job.get("root_job_id") or job["id"]
    root_uuid = _as_uuid(root_raw)
    rows = await pg_repo.get_history(session, root_uuid)
    emails_by_id = await _creator_emails(session, rows) if is_admin else {}
    jobs = [
        _job_row_to_public(
            r,
            mongo_repo.get_details(str(r["id"])),
            created_by_email=emails_by_id.get(_as_uuid(r["created_by"])),
        )
        for r in rows
    ]
    return ThumbnailHistoryResponse(jobs=jobs)


async def get_thumbnail_usage() -> ThumbnailUsageResponse:
    """Shared org-wide usage for the current calendar month, capped models only."""
    period_start = _start_of_current_month()
    usage = {
        model: ModelUsage(
            used=mongo_repo.count_by_model_since(model, period_start),
            limit=MONTHLY_MODEL_CAP,
        )
        for model in CAPPED_MODELS
    }
    usage["fluxkontext"] = ModelUsage(
        used=mongo_repo.count_by_model_since("fluxkontext", period_start),
        limit=None,
    )
    return ThumbnailUsageResponse(period_start=period_start, usage=usage)
