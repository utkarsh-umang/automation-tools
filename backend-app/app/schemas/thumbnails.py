"""HTTP schemas for thumbnail APIs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ThumbnailFeedbackRequest(BaseModel):
    feedback: str
    model: Literal["gptimage", "nanobanana", "fluxkontext"]


class ThumbnailJobCreatedResponse(BaseModel):
    id: uuid.UUID
    status: str


class ThumbnailSelectCandidateRequest(BaseModel):
    selected_url: str


class ThumbnailJobPublic(BaseModel):
    id: uuid.UUID
    status: str
    iteration: int
    result_url: str | None
    error: str | None
    parent_job_id: uuid.UUID | None
    root_job_id: uuid.UUID | None
    created_by: uuid.UUID
    created_by_email: str | None = None
    folder_id: uuid.UUID | None = None
    candidate_urls: list[str] | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    reference_image_url: str | None = None
    base_image_urls: list[str] | None = None
    title: str | None = None
    include_title: bool | None = None
    creative_comments: str | None = None
    model: str | None = None
    shorts_or_reels: bool | None = None
    feedback: str | None = None
    prompt_used: str | None = None


class ThumbnailListResponse(BaseModel):
    jobs: list[ThumbnailJobPublic]
    next_cursor: uuid.UUID | None = None


class ThumbnailHistoryResponse(BaseModel):
    jobs: list[ThumbnailJobPublic]


class ModelUsage(BaseModel):
    used: int
    limit: int | None
    """``limit=None`` means unlimited (e.g. fluxkontext)."""


class ThumbnailUsageResponse(BaseModel):
    """Shared org-wide monthly usage for capped models. Period is the current
    calendar month (UTC); resets automatically at the month boundary."""

    period_start: datetime
    usage: dict[str, ModelUsage]
