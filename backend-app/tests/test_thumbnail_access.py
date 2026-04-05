"""Unit tests for ``require_thumbnail_job_owner`` (SBL-20)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.thumbnail_access import require_thumbnail_job_owner

pytestmark = pytest.mark.anyio


def _row(created_by: uuid.UUID, job_id: uuid.UUID) -> dict:
    return {
        "id": job_id,
        "created_by": created_by,
        "status": "pending",
        "iteration": 1,
        "parent_job_id": None,
        "root_job_id": job_id,
        "result_url": None,
        "error": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "completed_at": None,
    }


@pytest.mark.asyncio
async def test_require_owner_404_missing() -> None:
    session = MagicMock()
    with patch(
        "app.services.thumbnail_access.pg_repo.get_job",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(HTTPException) as ei:
            await require_thumbnail_job_owner(session, uuid.uuid4(), uuid.uuid4())
        assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_require_owner_403_wrong_user() -> None:
    session = MagicMock()
    owner = uuid.uuid4()
    intruder = uuid.uuid4()
    job_id = uuid.uuid4()
    with patch(
        "app.services.thumbnail_access.pg_repo.get_job",
        new_callable=AsyncMock,
        return_value=_row(owner, job_id),
    ):
        with pytest.raises(HTTPException) as ei:
            await require_thumbnail_job_owner(session, job_id, intruder)
        assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_require_owner_ok() -> None:
    session = MagicMock()
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()
    row = _row(user_id, job_id)
    with patch(
        "app.services.thumbnail_access.pg_repo.get_job",
        new_callable=AsyncMock,
        return_value=row,
    ):
        out = await require_thumbnail_job_owner(session, job_id, user_id)
    assert out["id"] == job_id
