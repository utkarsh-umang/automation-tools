"""Thumbnail HTTP API — all routes require a valid JWT (``get_current_user``)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.config import config
from app.db.session import get_db_session
from app.schemas.thumbnails import (
    ThumbnailFeedbackRequest,
    ThumbnailHistoryResponse,
    ThumbnailJobCreatedResponse,
    ThumbnailJobPublic,
    ThumbnailListResponse,
    ThumbnailSelectCandidateRequest,
    ThumbnailUsageResponse,
)
from app.services import thumbnail_service

router = APIRouter()


async def _read_limited_image(
    f: UploadFile,
    *,
    field_label: str,
) -> tuple[bytes, str | None, str | None]:
    ctype = f.content_type
    base_ct = (ctype or "").split(";")[0].strip().lower()
    if not base_ct.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} must use an image/* content type",
        )
    body = await f.read()
    if len(body) > config.THUMBNAIL_INPUT_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"{field_label} exceeds maximum size "
                f"({config.THUMBNAIL_INPUT_MAX_BYTES} bytes)"
            ),
        )
    return body, f.filename, f.content_type


@router.post("", response_model=ThumbnailJobCreatedResponse)
async def create_thumbnail(
    reference_image: UploadFile,
    base_images: Annotated[list[UploadFile], File()] = [],
    title: str = Form(),
    include_title: bool = Form(),
    creative_comments: str = Form(),
    model: str = Form(),
    folder_id: uuid.UUID | None = Form(default=None),
    shorts_or_reels: bool = Form(default=False),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThumbnailJobCreatedResponse:
    """Create a thumbnail job from multipart uploads; ``created_by`` comes from the JWT only."""
    reference = await _read_limited_image(
        reference_image, field_label="reference_image"
    )
    base_tuples: list[tuple[bytes, str | None, str | None]] = []
    for idx, uf in enumerate(base_images):
        base_tuples.append(
            await _read_limited_image(uf, field_label=f"base_images[{idx}]")
        )
    return await thumbnail_service.create_thumbnail_job(
        db,
        uuid.UUID(current_user.id),
        reference=reference,
        base_images=base_tuples,
        title=title,
        include_title=include_title,
        creative_comments=creative_comments,
        model=model,
        folder_id=folder_id,
        shorts_or_reels=shorts_or_reels,
    )


@router.get("/usage", response_model=ThumbnailUsageResponse)
async def get_thumbnail_usage(
    _: CurrentUser = Depends(get_current_user),
) -> ThumbnailUsageResponse:
    """Shared org-wide monthly usage for the capped models (gptimage, nanobanana)."""
    return await thumbnail_service.get_thumbnail_usage()


@router.get("", response_model=ThumbnailListResponse)
async def list_thumbnails(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    cursor: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    folder_id: uuid.UUID | None = Query(None),
) -> ThumbnailListResponse:
    """ADMIN sees thumbnails from every member; MEMBER sees only their own."""
    return await thumbnail_service.list_thumbnail_jobs(
        db,
        uuid.UUID(current_user.id),
        cursor,
        limit,
        is_admin=current_user.role == "ADMIN",
        folder_id=folder_id,
    )


@router.post("/{job_id}/select", response_model=ThumbnailJobPublic)
async def select_thumbnail_candidate(
    job_id: uuid.UUID,
    body: ThumbnailSelectCandidateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThumbnailJobPublic:
    """Owner picks one of the generated candidates as the final thumbnail."""
    return await thumbnail_service.select_thumbnail_candidate(
        db, uuid.UUID(current_user.id), job_id, body.selected_url
    )


@router.post("/{job_id}/feedback", response_model=ThumbnailJobCreatedResponse)
async def feedback_thumbnail(
    job_id: uuid.UUID,
    body: ThumbnailFeedbackRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThumbnailJobCreatedResponse:
    return await thumbnail_service.submit_thumbnail_feedback(
        db, uuid.UUID(current_user.id), job_id, body
    )


@router.get("/{job_id}/history", response_model=ThumbnailHistoryResponse)
async def history_thumbnail(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThumbnailHistoryResponse:
    return await thumbnail_service.get_thumbnail_history(
        db, uuid.UUID(current_user.id), job_id, is_admin=current_user.role == "ADMIN"
    )


@router.get("/{job_id}", response_model=ThumbnailJobPublic)
async def get_thumbnail(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThumbnailJobPublic:
    return await thumbnail_service.get_thumbnail_job(
        db, uuid.UUID(current_user.id), job_id, is_admin=current_user.role == "ADMIN"
    )
