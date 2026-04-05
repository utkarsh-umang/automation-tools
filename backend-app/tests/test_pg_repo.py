"""Unit tests for ``pg_repo`` (mocked AsyncSession)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.thumbnail_job import ThumbnailJob
from app.repositories import pg_repo


def _async_session_mock() -> MagicMock:
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_create_job_adds_and_flushes() -> None:
    session = _async_session_mock()
    job_id = uuid.uuid4()
    user_id = uuid.uuid4()
    await pg_repo.create_job(session, job_id, user_id, None, None, 1)
    session.add.assert_called_once()
    added = session.add.call_args[0][0]
    assert isinstance(added, ThumbnailJob)
    assert added.id == job_id
    assert added.created_by == user_id
    assert added.iteration == 1
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_job_found() -> None:
    session = _async_session_mock()
    job_id = uuid.uuid4()
    now = datetime.now(UTC)
    job = ThumbnailJob(
        id=job_id,
        status="pending",
        created_by=uuid.uuid4(),
        iteration=1,
        created_at=now,
        updated_at=now,
    )
    session.get = AsyncMock(return_value=job)
    out = await pg_repo.get_job(session, job_id)
    assert out is not None
    assert out["id"] == job_id
    assert out["status"] == "pending"
    session.get.assert_awaited_once_with(ThumbnailJob, job_id)


@pytest.mark.asyncio
async def test_get_job_missing() -> None:
    session = _async_session_mock()
    session.get = AsyncMock(return_value=None)
    out = await pg_repo.get_job(session, uuid.uuid4())
    assert out is None


@pytest.mark.asyncio
async def test_update_status_executes() -> None:
    session = _async_session_mock()
    job_id = uuid.uuid4()
    await pg_repo.update_status(session, job_id, "running")
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_completed_executes() -> None:
    session = _async_session_mock()
    job_id = uuid.uuid4()
    await pg_repo.update_completed(session, job_id, "https://cdn.example/x.png")
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_failed_executes() -> None:
    session = _async_session_mock()
    job_id = uuid.uuid4()
    await pg_repo.update_failed(session, job_id, "boom")
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_jobs_by_user_no_cursor() -> None:
    session = _async_session_mock()
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    j1 = ThumbnailJob(
        id=uuid.uuid4(),
        status="pending",
        created_by=user_id,
        iteration=1,
        created_at=now,
        updated_at=now,
    )
    result = MagicMock()
    result.scalars.return_value.all.return_value = [j1]
    session.execute = AsyncMock(return_value=result)
    rows = await pg_repo.list_jobs_by_user(session, user_id, None, 10)
    assert len(rows) == 1
    assert rows[0]["id"] == j1.id


@pytest.mark.asyncio
async def test_list_jobs_by_user_bad_cursor_returns_empty() -> None:
    session = _async_session_mock()
    session.get = AsyncMock(return_value=None)
    rows = await pg_repo.list_jobs_by_user(
        session, uuid.uuid4(), uuid.uuid4(), 5
    )
    assert rows == []
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_get_history() -> None:
    session = _async_session_mock()
    root = uuid.uuid4()
    now = datetime.now(UTC)
    j1 = ThumbnailJob(
        id=root,
        status="completed",
        created_by=uuid.uuid4(),
        root_job_id=root,
        iteration=1,
        created_at=now,
        updated_at=now,
    )
    result = MagicMock()
    result.scalars.return_value.all.return_value = [j1]
    session.execute = AsyncMock(return_value=result)
    rows = await pg_repo.get_history(session, root)
    assert len(rows) == 1
    assert rows[0]["id"] == root


@pytest.mark.asyncio
async def test_list_jobs_by_user_with_cursor_filters() -> None:
    """Second page uses keyset: jobs strictly before cursor job by (created_at, id)."""
    session = _async_session_mock()
    user_id = uuid.uuid4()
    cursor_id = uuid.uuid4()
    t1 = datetime(2026, 1, 2, tzinfo=UTC)
    cursor_job = ThumbnailJob(
        id=cursor_id,
        status="pending",
        created_by=user_id,
        iteration=1,
        created_at=t1,
        updated_at=t1,
    )
    session.get = AsyncMock(return_value=cursor_job)
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    await pg_repo.list_jobs_by_user(session, user_id, cursor_id, 3)
    session.execute.assert_awaited_once()


def test_job_to_dict_covers_keys() -> None:
    jid = uuid.uuid4()
    uid = uuid.uuid4()
    now = datetime.now(UTC)
    job = ThumbnailJob(
        id=jid,
        status="pending",
        created_by=uid,
        iteration=2,
        created_at=now,
        updated_at=now,
    )
    d = pg_repo._job_to_dict(job)
    assert set(d.keys()) == {
        "id",
        "status",
        "created_by",
        "parent_job_id",
        "root_job_id",
        "iteration",
        "result_url",
        "error",
        "created_at",
        "updated_at",
        "completed_at",
    }
