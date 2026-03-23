"""Pydantic models for the yt_leads MongoDB collection."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EmailStatus(str, Enum):
    FOUND = "found"
    CAPTCHA = "captcha"
    NONE = "none"


class LeadDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, alias="_id")
    batchId: str
    searchTermId: str
    channelName: str
    channelUrl: str
    channelId: str
    subscribers: int
    uploadsLast30d: int
    avgViews: int
    lastUpload: str | None = None
    score: float
    country: str = ""
    email: str = ""
    emailStatus: EmailStatus = EmailStatus.NONE
    discoveredAt: datetime = Field(default_factory=datetime.utcnow)
