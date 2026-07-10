"""PostgreSQL ``thumbnail_jobs`` table (see Alembic migrations)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import ARRAY, Column, DateTime, Text, text
from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(UTC)


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
    folder_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="thumbnail_folders.id",
    )
    candidate_urls: list[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(Text()), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
