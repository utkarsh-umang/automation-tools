"""HTTP schemas for the thumbnail folders API (shared org-wide client style folders)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    style_prompt: str = ""


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    style_prompt: str | None = None


class FolderPublic(BaseModel):
    id: uuid.UUID
    name: str
    style_prompt: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FolderListResponse(BaseModel):
    folders: list[FolderPublic]
