"""Pydantic models for the yt_job_logs MongoDB collection."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobLogDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, alias="_id")
    batchId: str
    searchTermId: str | None = None
    event: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
