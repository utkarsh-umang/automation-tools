"""SBL-21–22: thumbnail integration tests (real Postgres + Mongo test DB).

The async pipeline ``_async_generate_thumbnail`` is invoked directly so it shares
the test event loop with SQLAlchemy/asyncpg; the Celery wrapper only adds
``asyncio.run`` (see ``generate_thumbnail_task``).
"""

from __future__ import annotations

import base64
import time
import uuid
from typing import Any

import pytest
from httpx import AsyncClient

from app.core.config import config
from app.db.session import AsyncSessionLocal
from app.repositories import mongo_repo, pg_repo
from app.worker.thumbnail.generate import _async_generate_thumbnail


def _mongo_reachable() -> bool:
    try:
        from pymongo import MongoClient

        client = MongoClient(
            config.MONGO_LOCAL_URI,
            serverSelectionTimeoutMS=2500,
        )
        client.admin.command("ping")
        client.close()
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.anyio,
    pytest.mark.integration,
    pytest.mark.skipif(
        not _mongo_reachable(),
        reason="MongoDB not reachable (e.g. start local Mongo or set MONGO_LOCAL_URI)",
    ),
]


# A real (decodable) 1x1 PNG. The inputs are decoded at the edge now, so an
# 8-byte signature is no longer a stand-in for an image.
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmM"
    "IQAAAABJRU5ErkJggg=="
)


def _create_thumb_multipart() -> dict[str, Any]:
    return {
        "files": [
            ("reference_image", ("ref.png", _PNG, "image/png")),
            ("base_images", ("b.png", _PNG, "image/png")),
        ],
        "data": {
            "title": "T",
            "include_title": "true",
            "creative_comments": "original-line",
            "model": "gptimage",
        },
    }

_DUMMY_S3_URLS = [
    "https://integration-test.invalid/out-0.png",
    "https://integration-test.invalid/out-1.png",
]
_DUMMY_PROMPT = "dummy-prompt-used"

# Must match ``thumbnail_creator_router`` mount: /api/v1/thumbnails + /thumbnail
_THUMB_BASE = "/api/v1/thumbnails/thumbnail"


async def _run_thumbnail_pipeline(job_id: str) -> None:
    """Run the same async pipeline as the Celery task (shared event loop as FastAPI tests)."""
    await _async_generate_thumbnail(job_id, time.perf_counter())


async def _login(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/users/seed",
        json={"email": "admin-thumb-int@test.com", "password": "adminpass"},
    )
    return await _login(client, "admin-thumb-int@test.com", "adminpass")


async def _member_headers(client: AsyncClient, admin_h: dict[str, str]) -> dict[str, str]:
    email = f"member-{uuid.uuid4().hex[:8]}@test.com"
    r = await client.post(
        "/api/v1/users",
        json={"email": email, "password": "pass", "role": "MEMBER"},
        headers=admin_h,
    )
    assert r.status_code == 201, r.text
    return await _login(client, email, "pass")


async def _load_pg(job_id: str) -> dict[str, Any] | None:
    async with AsyncSessionLocal() as session:
        return await pg_repo.get_job(session, uuid.UUID(job_id))


@pytest.fixture(autouse=True)
def thumbnail_route_mongo_to_test_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Store thumbnail_job_details in ``MONGO_TEST_DB_NAME``; isolate from dev data."""

    def routed_get_database_connection(
        db_name: str | None = None,
        is_test_write: bool = False,
    ) -> Any:
        from app.mongo.connection_manager import get_mongo_manager

        return get_mongo_manager().get_connection(
            db_name=db_name or config.MONGO_TEST_DB_NAME,
            is_test_write=is_test_write,
        )

    monkeypatch.setattr(
        "app.repositories.mongo_repo.get_database_connection",
        routed_get_database_connection,
    )
    coll = mongo_repo._collection()
    coll.delete_many({})
    mongo_repo.ensure_thumbnail_job_details_indexes()


@pytest.fixture
def stub_agent_and_s3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.thumbnail_service.upload_to_s3",
        lambda _data, key: f"https://integration-input.invalid/{key}",
    )

    def _agent(**_kwargs: Any) -> dict[str, Any]:
        return {
            "images": [b"\x89PNG\r\n\x1a\n", b"\x89PNG\r\n\x1a\n2"],
            "prompt_used": _DUMMY_PROMPT,
        }

    monkeypatch.setattr("ai_agents.run_thumbnail_agent", _agent)
    monkeypatch.setattr(
        "app.worker.thumbnail.generate.get_s3_object_read_url",
        lambda key: f"https://integration-read.invalid/{key}",
    )
    monkeypatch.setattr(
        "app.worker.thumbnail.generate.upload_thumbnail_png_candidate",
        lambda _jid, index, _data: _DUMMY_S3_URLS[index],
    )


@pytest.fixture
def capture_celery_delay(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    queued: list[str] = []

    def _delay(job_id: str) -> None:
        queued.append(job_id)

    monkeypatch.setattr(
        "app.worker.thumbnail.generate.generate_thumbnail_task.delay",
        _delay,
    )
    return queued


@pytest.fixture
def track_pg_status(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    statuses: list[str] = []
    real_update = pg_repo.update_status

    async def _wrap(
        session: Any,
        job_id: uuid.UUID,
        status: str,
    ) -> None:
        statuses.append(status)
        await real_update(session, job_id, status)

    monkeypatch.setattr(pg_repo, "update_status", _wrap)
    return statuses


async def test_full_job_lifecycle_happy_path(
    client: AsyncClient,
    capture_celery_delay: list[str],
    stub_agent_and_s3: None,
    track_pg_status: list[str],
) -> None:
    admin_h = await _admin_headers(client)
    member_h = await _member_headers(client, admin_h)

    r = await client.post(
        _THUMB_BASE,
        headers=member_h,
        **_create_thumb_multipart(),
    )
    assert r.status_code == 200, r.text
    job_id = r.json()["id"]
    assert capture_celery_delay == [job_id]

    row = await _load_pg(job_id)
    assert row is not None
    assert row["status"] == "pending"
    assert row["result_url"] is None

    doc = mongo_repo.get_details(job_id)
    assert doc is not None
    assert doc.get("model") == "gptimage"
    assert doc.get("creative_comments") == "original-line"
    assert doc.get("prompt_used") in (None, "")
    assert doc.get("reference_image_s3_key") == (
        f"thumbnail-inputs/{job_id}/reference.png"
    )
    assert doc.get("base_image_s3_keys") == [
        f"thumbnail-inputs/{job_id}/base/0.png",
    ]

    await _run_thumbnail_pipeline(job_id)

    assert "processing" in track_pg_status

    row = await _load_pg(job_id)
    assert row is not None
    assert row["status"] == "awaiting_selection"
    assert row["result_url"] is None
    assert row["candidate_urls"] == _DUMMY_S3_URLS
    assert row.get("error") in (None, "")

    doc = mongo_repo.get_details(job_id)
    assert doc is not None
    assert doc.get("prompt_used") == _DUMMY_PROMPT

    sr = await client.post(
        f"{_THUMB_BASE}/{job_id}/select",
        json={"selected_url": _DUMMY_S3_URLS[0]},
        headers=member_h,
    )
    assert sr.status_code == 200, sr.text

    row = await _load_pg(job_id)
    assert row is not None
    assert row["status"] == "completed"
    assert row["result_url"] == _DUMMY_S3_URLS[0]


async def test_feedback_lineage_and_merged_comments(
    client: AsyncClient,
    capture_celery_delay: list[str],
    stub_agent_and_s3: None,
) -> None:
    admin_h = await _admin_headers(client)
    member_h = await _member_headers(client, admin_h)

    cr = await client.post(
        _THUMB_BASE,
        headers=member_h,
        **_create_thumb_multipart(),
    )
    assert cr.status_code == 200, cr.text
    job1 = cr.json()["id"]
    await _run_thumbnail_pipeline(job1)
    sr1 = await client.post(
        f"{_THUMB_BASE}/{job1}/select",
        json={"selected_url": _DUMMY_S3_URLS[0]},
        headers=member_h,
    )
    assert sr1.status_code == 200, sr1.text

    row1 = await _load_pg(job1)
    assert row1 is not None
    assert row1["status"] == "completed"
    root1 = row1.get("root_job_id") or row1["id"]

    capture_celery_delay.clear()
    fr = await client.post(
        f"{_THUMB_BASE}/{job1}/feedback",
        json={"feedback": "round-two", "model": "gptimage"},
        headers=member_h,
    )
    assert fr.status_code == 200, fr.text
    job2 = fr.json()["id"]
    assert capture_celery_delay == [job2]

    row2_pending = await _load_pg(job2)
    assert row2_pending is not None
    assert row2_pending["status"] == "pending"

    doc2_pending = mongo_repo.get_details(job2)
    assert doc2_pending is not None
    assert "original-line" in doc2_pending.get("creative_comments", "")
    assert "Latest revision request: round-two" in doc2_pending.get("creative_comments", "")

    await _run_thumbnail_pipeline(job2)
    sr2 = await client.post(
        f"{_THUMB_BASE}/{job2}/select",
        json={"selected_url": _DUMMY_S3_URLS[0]},
        headers=member_h,
    )
    assert sr2.status_code == 200, sr2.text

    row2 = await _load_pg(job2)
    assert row2 is not None
    assert row2["status"] == "completed"
    assert uuid.UUID(str(row2["parent_job_id"])) == uuid.UUID(job1)
    assert uuid.UUID(str(row2["root_job_id"])) == uuid.UUID(str(root1))
    assert row2["iteration"] == 2

    capture_celery_delay.clear()
    fr2 = await client.post(
        f"{_THUMB_BASE}/{job2}/feedback",
        json={"feedback": "round-three", "model": "gptimage"},
        headers=member_h,
    )
    assert fr2.status_code == 200, fr2.text
    job3 = fr2.json()["id"]
    assert capture_celery_delay == [job3]

    doc3_before = mongo_repo.get_details(job3)
    assert doc3_before is not None
    # Each iteration's prompt is built from the ROOT job's original creative
    # direction plus only the newest feedback — round-two's feedback must NOT
    # still be present here, otherwise feedback is stacking across iterations
    # instead of being replaced.
    assert "original-line" in doc3_before.get("creative_comments", "")
    assert "Latest revision request: round-three" in doc3_before.get("creative_comments", "")
    assert "round-two" not in doc3_before.get("creative_comments", "")

    await _run_thumbnail_pipeline(job3)
    sr3 = await client.post(
        f"{_THUMB_BASE}/{job3}/select",
        json={"selected_url": _DUMMY_S3_URLS[1]},
        headers=member_h,
    )
    assert sr3.status_code == 200, sr3.text

    row3 = await _load_pg(job3)
    assert row3 is not None
    assert row3["status"] == "completed"
    assert row3["result_url"] == _DUMMY_S3_URLS[1]
    assert row3["iteration"] == 3
    assert uuid.UUID(str(row3["root_job_id"])) == uuid.UUID(str(root1))
    assert uuid.UUID(str(row3["parent_job_id"])) == uuid.UUID(job2)
