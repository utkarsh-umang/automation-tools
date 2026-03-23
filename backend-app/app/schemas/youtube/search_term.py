"""Pydantic models for the yt_search_terms MongoDB collection."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TermStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class SearchTermDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, alias="_id")
    batchId: str
    term: str
    status: TermStatus = TermStatus.PENDING
    position: int = 0
    creditsUsed: int = 0
    channelsDiscovered: int = 0
    channelsQualified: int = 0
    emailsFound: int = 0
    startedAt: datetime | None = None
    completedAt: datetime | None = None
    errorMessage: str | None = None
