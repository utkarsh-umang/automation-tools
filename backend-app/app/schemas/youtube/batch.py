"""Pydantic models for the yt_batches MongoDB collection."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class BatchStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchFilters(BaseModel):
    minSubs: int = 0
    maxSubs: int = 1_000_000
    minUploadsLast30d: int = 1
    minAvgViews: int = 0
    excludeCountries: list[str] = ["IN"]
    region: str = "US"


class BatchDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, alias="_id")
    name: str
    keyword: str
    status: BatchStatus = BatchStatus.QUEUED
    filters: BatchFilters
    totalTerms: int = 0
    processedTerms: int = 0
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    lastTriggeredAt: datetime | None = None
    completedAt: datetime | None = None
