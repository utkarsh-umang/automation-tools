"""Thumbnail HTTP API — all routes require a valid JWT (``get_current_user``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db_session
from app.schemas.thumbnails import (
    ThumbnailCreateRequest,
    ThumbnailFeedbackRequest,
    ThumbnailHistoryResponse,
    ThumbnailJobCreatedResponse,
    ThumbnailJobPublic,
    ThumbnailListResponse,
)
from app.services import thumbnail_service

router = APIRouter()


@router.post("", response_model=ThumbnailJobCreatedResponse)
async def create_thumbnail(
    body: ThumbnailCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThumbnailJobCreatedResponse:
    """Create a thumbnail job; ``created_by`` is taken from the JWT only."""
    return await thumbnail_service.create_thumbnail_job(
        db, uuid.UUID(current_user.id), body
    )


@router.get("", response_model=ThumbnailListResponse)
async def list_thumbnails(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    cursor: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> ThumbnailListResponse:
    return await thumbnail_service.list_thumbnail_jobs(
        db, uuid.UUID(current_user.id), cursor, limit
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
        db, uuid.UUID(current_user.id), job_id
    )


@router.get("/{job_id}", response_model=ThumbnailJobPublic)
async def get_thumbnail(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThumbnailJobPublic:
    return await thumbnail_service.get_thumbnail_job(
        db, uuid.UUID(current_user.id), job_id
    )
