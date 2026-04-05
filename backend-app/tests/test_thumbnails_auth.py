"""Thumbnail API auth and ownership (EP-06 / SBL-19–20)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio

_PNG = b"\x89PNG\r\n\x1a\n"

_THUMB_CREATE_KWARGS: dict[str, Any] = {
    "files": [
        ("reference_image", ("ref.png", _PNG, "image/png")),
        ("base_images", ("b.png", _PNG, "image/png")),
    ],
    "data": {
        "title": "T",
        "include_title": "true",
        "creative_comments": "c",
        "model": "gptimage",
    },
}


@pytest.fixture
def mongo_memory(monkeypatch: pytest.MonkeyPatch) -> dict[str, dict]:
    store: dict[str, dict] = {}

    def _create(job_id: str, payload: dict, *, db_name: str | None = None) -> None:
        store[job_id] = {"job_id": job_id, **dict(payload)}

    def _get(job_id: str, *, db_name: str | None = None) -> dict | None:
        doc = store.get(job_id)
        return dict(doc) if doc else None

    monkeypatch.setattr("app.repositories.mongo_repo.create_details", _create)
    monkeypatch.setattr("app.repositories.mongo_repo.get_details", _get)
    return store


@pytest.fixture
def stub_celery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.worker.thumbnail.generate.generate_thumbnail_task.delay",
        MagicMock(),
    )


@pytest.fixture
def stub_s3_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake(_data: bytes, key: str) -> str:
        return f"https://fake-s3.invalid/{key}"

    monkeypatch.setattr("app.services.thumbnail_service.upload_to_s3", _fake)


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
        json={"email": "admin-thumb@test.com", "password": "adminpass"},
    )
    return await _login(client, "admin-thumb@test.com", "adminpass")


async def _create_member(
    client: AsyncClient, admin_h: dict[str, str], email: str, password: str
) -> dict[str, str]:
    r = await client.post(
        "/api/v1/users",
        json={"email": email, "password": password, "role": "MEMBER"},
        headers=admin_h,
    )
    assert r.status_code == 201, r.text
    return await _login(client, email, password)


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("post", "/api/v1/thumbnails", _THUMB_CREATE_KWARGS),
        ("get", "/api/v1/thumbnails", {}),
        ("get", "/api/v1/thumbnails/00000000-0000-4000-8000-000000000001", {}),
        (
            "post",
            "/api/v1/thumbnails/00000000-0000-4000-8000-000000000001/feedback",
            {"json": {"feedback": "x", "model": "gptimage"}},
        ),
        (
            "get",
            "/api/v1/thumbnails/00000000-0000-4000-8000-000000000001/history",
            {},
        ),
    ],
)
async def test_thumbnail_endpoints_reject_invalid_token(
    client: AsyncClient,
    method: str,
    path: str,
    kwargs: dict,
) -> None:
    headers = {"Authorization": "Bearer not-a-real-jwt"}
    r = await client.request(method, path, headers=headers, **kwargs)
    assert r.status_code == 401


async def test_cross_user_get_thumbnail_forbidden(
    client: AsyncClient,
    mongo_memory: dict[str, dict],
    stub_celery: None,
    stub_s3_upload: None,
) -> None:
    adm = await _admin_headers(client)
    h_a = await _create_member(client, adm, "owner@test.com", "pass1")
    h_b = await _create_member(client, adm, "other@test.com", "pass2")

    cr = await client.post(
        "/api/v1/thumbnails",
        headers=h_a,
        **_THUMB_CREATE_KWARGS,
    )
    assert cr.status_code == 200, cr.text
    job_id = cr.json()["id"]

    gr = await client.get(f"/api/v1/thumbnails/{job_id}", headers=h_b)
    assert gr.status_code == 403

    fr = await client.post(
        f"/api/v1/thumbnails/{job_id}/feedback",
        json={"feedback": "more", "model": "gptimage"},
        headers=h_b,
    )
    assert fr.status_code == 403

    hr = await client.get(f"/api/v1/thumbnails/{job_id}/history", headers=h_b)
    assert hr.status_code == 403


async def test_owner_can_read_thumbnail(
    client: AsyncClient,
    mongo_memory: dict[str, dict],
    stub_celery: None,
    stub_s3_upload: None,
) -> None:
    adm = await _admin_headers(client)
    h = await _create_member(client, adm, "solo@test.com", "solo")
    cr = await client.post(
        "/api/v1/thumbnails",
        headers=h,
        **_THUMB_CREATE_KWARGS,
    )
    job_id = cr.json()["id"]
    expected_ref = f"https://fake-s3.invalid/thumbnail-inputs/{job_id}/reference.png"
    gr = await client.get(f"/api/v1/thumbnails/{job_id}", headers=h)
    assert gr.status_code == 200
    assert gr.json()["id"] == job_id
    assert gr.json()["reference_image_url"] == expected_ref
