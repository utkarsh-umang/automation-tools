"""Pydantic models for the yt_daily_usage MongoDB collection."""

from pydantic import BaseModel, ConfigDict, Field


class DailyUsageDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, alias="_id")
    date: str  # "YYYY-MM-DD"
    creditsUsed: int = 0
    creditLimit: int = 10000
    activeBatchId: str | None = None
    runsCompleted: int = 0
