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
from sqlalchemy.orm import aliased

from app.models.thumbnail_job import ThumbnailJob


def _lineage_key():
    """Identifier that groups every iteration of one thumbnail together.

    A lineage is keyed by ``root_job_id``; the root job itself has a null
    ``root_job_id`` in some older rows, so fall back to its own ``id``.
    """
    return func.coalesce(ThumbnailJob.root_job_id, ThumbnailJob.id)


def _apply_folder_filter(stmt, folder_id, include_unfoldered):
    """Scope a jobs query to a folder.

    ``include_unfoldered`` widens the match to also pull in jobs with no folder
    (``folder_id IS NULL``) — used for the "Testing" bucket, which funnels both
    its own jobs and every unfiled thumbnail.
    """
    if folder_id is not None:
        if include_unfoldered:
            return stmt.where(
                or_(
                    ThumbnailJob.folder_id == folder_id,
                    ThumbnailJob.folder_id.is_(None),
                )
            )
        return stmt.where(ThumbnailJob.folder_id == folder_id)
    if include_unfoldered:
        return stmt.where(ThumbnailJob.folder_id.is_(None))
    return stmt


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
    *,
    roots_only: bool = False,
    include_unfoldered: bool = False,
) -> list[dict[str, Any]]:
    """``user_id=None`` lists jobs across all users (ADMIN-only callers).

    ``roots_only`` collapses each thumbnail's iteration chain to a single row —
    its latest iteration — so the list shows one card per lineage instead of one
    per regeneration. Cursor pagination still works: the cursor is the last
    representative row's ``id``.
    """
    if roots_only:
        # One row per lineage: DISTINCT ON the lineage key, keeping the highest
        # iteration. Wrap in a subquery so the outer page can re-order the
        # representatives by recency and apply the cursor window.
        lineage_key = _lineage_key()
        inner = select(ThumbnailJob)
        if user_id is not None:
            inner = inner.where(ThumbnailJob.created_by == user_id)
        inner = _apply_folder_filter(inner, folder_id, include_unfoldered)
        inner = inner.distinct(lineage_key).order_by(
            lineage_key,
            ThumbnailJob.iteration.desc(),
            ThumbnailJob.created_at.desc(),
            ThumbnailJob.id.desc(),
        )
        latest = aliased(ThumbnailJob, inner.subquery())
        stmt = select(latest)
        if cursor is not None:
            cur_job = await session.get(ThumbnailJob, cursor)
            if cur_job is None:
                return []
            stmt = stmt.where(
                or_(
                    latest.created_at < cur_job.created_at,
                    and_(
                        latest.created_at == cur_job.created_at,
                        latest.id < cursor,
                    ),
                )
            )
        stmt = stmt.order_by(latest.created_at.desc(), latest.id.desc()).limit(limit)
        result = await session.execute(stmt)
        return [_job_to_dict(r) for r in result.scalars().all()]

    stmt = select(ThumbnailJob)
    if user_id is not None:
        stmt = stmt.where(ThumbnailJob.created_by == user_id)
    stmt = _apply_folder_filter(stmt, folder_id, include_unfoldered)
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


async def folder_lineage_summaries(
    session: AsyncSession,
    user_id: uuid.UUID | None,
) -> list[dict[str, Any]]:
    """Per-folder lineage count + a cover image, for the folder album grid.

    Returns one entry per folder plus one for the unfoldered bucket
    (``folder_id`` is ``None`` there). ``count`` is the number of distinct
    lineages (matching the one-card-per-lineage list); ``cover_url`` is the most
    recent image in that folder. ``user_id=None`` spans all users (ADMIN).
    """
    lineage_key = _lineage_key()

    count_stmt = select(
        ThumbnailJob.folder_id,
        func.count(func.distinct(lineage_key)).label("cnt"),
    )
    if user_id is not None:
        count_stmt = count_stmt.where(ThumbnailJob.created_by == user_id)
    count_stmt = count_stmt.group_by(ThumbnailJob.folder_id)
    count_rows = (await session.execute(count_stmt)).all()

    # Newest job carrying an image, per folder → the tile's cover.
    cover_stmt = select(
        ThumbnailJob.folder_id,
        ThumbnailJob.result_url,
        ThumbnailJob.candidate_urls,
    ).where(
        or_(
            ThumbnailJob.result_url.is_not(None),
            ThumbnailJob.candidate_urls.is_not(None),
        )
    )
    if user_id is not None:
        cover_stmt = cover_stmt.where(ThumbnailJob.created_by == user_id)
    cover_stmt = cover_stmt.distinct(ThumbnailJob.folder_id).order_by(
        ThumbnailJob.folder_id,
        ThumbnailJob.created_at.desc(),
        ThumbnailJob.id.desc(),
    )
    covers: dict[uuid.UUID | None, str | None] = {}
    for fid, result_url, candidate_urls in (await session.execute(cover_stmt)).all():
        covers[fid] = result_url or (candidate_urls[0] if candidate_urls else None)

    return [
        {"folder_id": fid, "count": int(cnt), "cover_url": covers.get(fid)}
        for fid, cnt in count_rows
    ]


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
