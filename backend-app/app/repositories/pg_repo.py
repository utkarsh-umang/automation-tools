"""PostgreSQL access for ``thumbnail_jobs``.

Callers pass an :class:`~sqlalchemy.ext.asyncio.AsyncSession`; this module performs
all SQL for thumbnail jobs (no raw SQL elsewhere in the app for this table).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.thumbnail_job import ThumbnailJob


def _job_to_dict(job: ThumbnailJob) -> dict[str, Any]:
    return {
        "id": job.id,
        "status": job.status,
        "created_by": job.created_by,
        "parent_job_id": job.parent_job_id,
        "root_job_id": job.root_job_id,
        "iteration": job.iteration,
        "result_url": job.result_url,
        "error": job.error,
        "folder_id": job.folder_id,
        "candidate_urls": job.candidate_urls,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "completed_at": job.completed_at,
    }


async def create_job(
    session: AsyncSession,
    job_id: uuid.UUID,
    created_by: uuid.UUID,
    parent_job_id: uuid.UUID | None,
    root_job_id: uuid.UUID | None,
    iteration: int,
    folder_id: uuid.UUID | None = None,
) -> None:
    job = ThumbnailJob(
        id=job_id,
        created_by=created_by,
        parent_job_id=parent_job_id,
        root_job_id=root_job_id,
        iteration=iteration,
        folder_id=folder_id,
    )
    session.add(job)
    await session.flush()


async def get_job(session: AsyncSession, job_id: uuid.UUID) -> dict[str, Any] | None:
    row = await session.get(ThumbnailJob, job_id)
    return _job_to_dict(row) if row else None


async def update_status(
    session: AsyncSession, job_id: uuid.UUID, status: str
) -> None:
    await session.execute(
        update(ThumbnailJob)
        .where(ThumbnailJob.id == job_id)
        .values(status=status, updated_at=func.now())
    )


async def update_completed(
    session: AsyncSession, job_id: uuid.UUID, result_url: str
) -> None:
    await session.execute(
        update(ThumbnailJob)
        .where(ThumbnailJob.id == job_id)
        .values(
            result_url=result_url,
            status="completed",
            completed_at=func.now(),
            updated_at=func.now(),
        )
    )


async def update_candidates(
    session: AsyncSession, job_id: uuid.UUID, candidate_urls: list[str]
) -> None:
    """Generation produced candidates; job now awaits the caller picking one."""
    await session.execute(
        update(ThumbnailJob)
        .where(ThumbnailJob.id == job_id)
        .values(
            candidate_urls=candidate_urls,
            status="awaiting_selection",
            updated_at=func.now(),
        )
    )


async def update_failed(
    session: AsyncSession, job_id: uuid.UUID, error: str
) -> None:
    await session.execute(
        update(ThumbnailJob)
        .where(ThumbnailJob.id == job_id)
        .values(error=error, status="failed", updated_at=func.now())
    )


async def list_stale_processing(
    session: AsyncSession, older_than_minutes: int
) -> list[dict[str, Any]]:
    """Jobs stuck in ``processing`` longer than a hard-time-limit worker kill

    could ever leave one, un-reaped. Backstop for the watchdog: a hard
    time-limit kill (SIGKILL) bypasses all Python cleanup, so a job can be
    orphaned in ``processing`` forever with no failure recorded.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
    stmt = select(ThumbnailJob).where(
        ThumbnailJob.status == "processing",
        ThumbnailJob.updated_at < cutoff,
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [_job_to_dict(r) for r in rows]


async def list_jobs_by_user(
    session: AsyncSession,
    user_id: uuid.UUID | None,
    cursor: uuid.UUID | None,
    limit: int,
    folder_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    """``user_id=None`` lists jobs across all users (ADMIN-only callers)."""
    stmt = select(ThumbnailJob)
    if user_id is not None:
        stmt = stmt.where(ThumbnailJob.created_by == user_id)
    if folder_id is not None:
        stmt = stmt.where(ThumbnailJob.folder_id == folder_id)
    if cursor is not None:
        cur_job = await session.get(ThumbnailJob, cursor)
        if cur_job is None:
            return []
        stmt = stmt.where(
            or_(
                ThumbnailJob.created_at < cur_job.created_at,
                and_(
                    ThumbnailJob.created_at == cur_job.created_at,
                    ThumbnailJob.id < cur_job.id,
                ),
            )
        )
    stmt = (
        stmt.order_by(ThumbnailJob.created_at.desc(), ThumbnailJob.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [_job_to_dict(r) for r in rows]


async def get_history(
    session: AsyncSession, root_job_id: uuid.UUID
) -> list[dict[str, Any]]:
    stmt = (
        select(ThumbnailJob)
        .where(
            or_(
                ThumbnailJob.root_job_id == root_job_id,
                ThumbnailJob.id == root_job_id,
            )
        )
        .order_by(ThumbnailJob.iteration.asc(), ThumbnailJob.created_at.asc())
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [_job_to_dict(r) for r in rows]
