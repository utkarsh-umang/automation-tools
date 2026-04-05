"""HTTP schemas for thumbnail APIs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ThumbnailCreateRequest(BaseModel):
    """Create body — never includes ``created_by`` (comes from JWT)."""

    reference_image_url: str
    base_image_urls: list[str]
    title: str
    include_title: bool
    creative_comments: str
    model: Literal["gptimage", "nanobanana"]


class ThumbnailFeedbackRequest(BaseModel):
    feedback: str
    model: Literal["gptimage", "nanobanana"]


class ThumbnailJobCreatedResponse(BaseModel):
    id: uuid.UUID
    status: str


class ThumbnailJobPublic(BaseModel):
    id: uuid.UUID
    status: str
    iteration: int
    result_url: str | None
    error: str | None
    parent_job_id: uuid.UUID | None
    root_job_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    reference_image_url: str | None = None
    base_image_urls: list[str] | None = None
    title: str | None = None
    include_title: bool | None = None
    creative_comments: str | None = None
    model: str | None = None
    feedback: str | None = None
    prompt_used: str | None = None


class ThumbnailListResponse(BaseModel):
    jobs: list[ThumbnailJobPublic]
    next_cursor: uuid.UUID | None = None


class ThumbnailHistoryResponse(BaseModel):
    jobs: list[ThumbnailJobPublic]
