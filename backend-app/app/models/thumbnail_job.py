"""PostgreSQL ``thumbnail_jobs`` table (see Alembic migrations)."""

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class ThumbnailJob(SQLModel, table=True):
    __tablename__ = "thumbnail_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: str = Field(default="pending", max_length=20)
    created_by: uuid.UUID = Field(foreign_key="users.id")
    parent_job_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="thumbnail_jobs.id",
    )
    root_job_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="thumbnail_jobs.id",
    )
    iteration: int = Field(default=1)
    result_url: str | None = Field(default=None)
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)
