"""Repo-level tests for the folder-grid feature: latest-per-lineage listing
(``roots_only``) and the folder album summaries (count + cover image).

These run against the real Postgres test DB (see ``conftest``), so they exercise
the actual ``DISTINCT ON`` SQL rather than a mock.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.session import engine as app_engine
from app.models.thumbnail_folder import ThumbnailFolder
from app.models.thumbnail_job import ThumbnailJob
from app.models.user import User
from app.repositories import pg_repo

pytestmark = pytest.mark.anyio

_session = async_sessionmaker(bind=app_engine, expire_on_commit=False)

_T0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _job(
    *,
    created_by: uuid.UUID,
    root: uuid.UUID,
    iteration: int,
    minute: int,
    folder_id: uuid.UUID | None,
    result_url: str | None = None,
    candidate_urls: list[str] | None = None,
    parent: uuid.UUID | None = None,
) -> ThumbnailJob:
    ts = _T0 + timedelta(minutes=minute)
    return ThumbnailJob(
        id=root if iteration == 1 else uuid.uuid4(),
        created_by=created_by,
        parent_job_id=parent,
        root_job_id=root,
        iteration=iteration,
        folder_id=folder_id,
        result_url=result_url,
        candidate_urls=candidate_urls,
        created_at=ts,
        updated_at=ts,
    )


async def _seed() -> dict[str, uuid.UUID]:
    """One user, one folder, three lineages (A: 3 iters in folder, B: 1 iter in
    folder, C: 1 iter unfoldered). Returns the ids the tests assert on."""
    uid = uuid.uuid4()
    fid = uuid.uuid4()
    a_root = uuid.uuid4()
    b_root = uuid.uuid4()
    c_root = uuid.uuid4()

    async with _session() as s:
        # Flush in FK order (user → folder → jobs); no ORM relationships are
        # declared, so the unit-of-work can't infer the insert order itself.
        s.add(User(id=uid, email=f"u{uid.hex[:8]}@t.co", hashed_password="x"))
        await s.flush()
        s.add(
            ThumbnailFolder(
                id=fid, name="a2zfintech", style_prompt="", created_by=uid
            )
        )
        await s.flush()
        # Lineage A — 3 iterations in the folder; latest (iter 3) is newest overall.
        a1 = _job(created_by=uid, root=a_root, iteration=1, minute=1, folder_id=fid)
        a2 = _job(
            created_by=uid, root=a_root, iteration=2, minute=2, folder_id=fid,
            parent=a1.id,
        )
        a3 = _job(
            created_by=uid, root=a_root, iteration=3, minute=9, folder_id=fid,
            parent=a2.id, result_url="https://img/a3.png",
        )
        # Lineage B — single iteration in the folder, image is a candidate set.
        b1 = _job(
            created_by=uid, root=b_root, iteration=1, minute=3, folder_id=fid,
            candidate_urls=["https://img/b1.png"],
        )
        # Lineage C — single iteration, no folder (unfoldered bucket).
        c1 = _job(
            created_by=uid, root=c_root, iteration=1, minute=4, folder_id=None,
            result_url="https://img/c1.png",
        )
        for j in (a1, a2, a3, b1, c1):
            s.add(j)
        await s.commit()

    return {
        "uid": uid,
        "fid": fid,
        "a_root": a_root,
        "a3": a3.id,
        "b1": b1.id,
        "c1": c1.id,
    }


async def test_roots_only_collapses_to_latest_iteration() -> None:
    ids = await _seed()
    async with _session() as s:
        rows = await pg_repo.list_jobs_by_user(
            s, ids["uid"], None, 50, folder_id=ids["fid"], roots_only=True
        )
    by_id = {r["id"]: r for r in rows}
    # One row per lineage in the folder: A's latest (iter 3) and B (iter 1).
    assert set(by_id) == {ids["a3"], ids["b1"]}
    assert by_id[ids["a3"]]["iteration"] == 3
    assert by_id[ids["a3"]]["root_job_id"] == ids["a_root"]


async def test_roots_only_include_unfoldered_adds_the_bucket() -> None:
    ids = await _seed()
    async with _session() as s:
        rows = await pg_repo.list_jobs_by_user(
            s, ids["uid"], None, 50,
            folder_id=ids["fid"], roots_only=True, include_unfoldered=True,
        )
    assert {r["id"] for r in rows} == {ids["a3"], ids["b1"], ids["c1"]}


async def test_non_roots_list_returns_every_iteration() -> None:
    ids = await _seed()
    async with _session() as s:
        rows = await pg_repo.list_jobs_by_user(
            s, ids["uid"], None, 50, folder_id=ids["fid"]
        )
    # A's three iterations + B's one, all as separate rows.
    assert len(rows) == 4


async def test_roots_only_cursor_paginates() -> None:
    ids = await _seed()
    async with _session() as s:
        page1 = await pg_repo.list_jobs_by_user(
            s, ids["uid"], None, 1,
            folder_id=ids["fid"], roots_only=True, include_unfoldered=True,
        )
        assert len(page1) == 1
        cursor = page1[-1]["id"]
        page2 = await pg_repo.list_jobs_by_user(
            s, ids["uid"], cursor, 50,
            folder_id=ids["fid"], roots_only=True, include_unfoldered=True,
        )
    seen = {page1[0]["id"], *(r["id"] for r in page2)}
    assert seen == {ids["a3"], ids["b1"], ids["c1"]}
    assert page1[0]["id"] not in {r["id"] for r in page2}  # no overlap


async def test_folder_summaries_count_and_cover() -> None:
    ids = await _seed()
    async with _session() as s:
        summaries = await pg_repo.folder_lineage_summaries(s, ids["uid"])
    by_folder = {r["folder_id"]: r for r in summaries}
    # Folder holds two lineages; cover is the newest image in it (A's iter 3).
    assert by_folder[ids["fid"]]["count"] == 2
    assert by_folder[ids["fid"]]["cover_url"] == "https://img/a3.png"
    # Unfoldered bucket: one lineage, its own image.
    assert by_folder[None]["count"] == 1
    assert by_folder[None]["cover_url"] == "https://img/c1.png"
