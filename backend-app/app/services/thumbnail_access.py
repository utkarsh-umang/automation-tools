"""Shared access control for thumbnail jobs (EP-06 / SBL-20)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import pg_repo


async def require_thumbnail_job_owner(
    session: AsyncSession,
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    is_admin: bool = False,
) -> dict[str, Any]:
    """
    Load a thumbnail job and ensure ``created_by`` matches ``user_id``.

    Raises ``404`` if the job does not exist, ``403`` if it belongs to another user
    (so existence is not hidden as 404). ``is_admin`` bypasses the ownership check
    so ADMIN accounts can view (but not act on) any member's job.
    """
    job = await pg_repo.get_job(session, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail job not found",
        )
    if is_admin:
        return job
    owner = job["created_by"]
    if isinstance(owner, uuid.UUID):
        owner_id = owner
    else:
        owner_id = uuid.UUID(str(owner))
    if owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this thumbnail job",
        )
    return job
