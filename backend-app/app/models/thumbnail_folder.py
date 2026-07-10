"""PostgreSQL ``thumbnail_folders`` table (see Alembic migrations).

Shared org-wide: any authenticated user can read/use any folder. ``created_by``
is kept for audit only, not for access scoping.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, text
from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ThumbnailFolder(SQLModel, table=True):
    __tablename__ = "thumbnail_folders"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=200)
    style_prompt: str = Field(default="")
    created_by: uuid.UUID = Field(foreign_key="users.id")
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
