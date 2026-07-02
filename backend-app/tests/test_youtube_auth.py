"""YouTube API auth enforcement.

Regression guard for the P0 where the entire YouTube router was public. Auth is
enforced at the router level (``youtube_router`` has ``Depends(get_current_user)``),
so every endpoint must reject missing / invalid tokens.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio

_FAKE_ID = "00000000-0000-4000-8000-000000000001"

# (method, path) across every YouTube sub-router (batches, leads, credits).
_YOUTUBE_ENDPOINTS = [
    ("get", "/api/v1/youtube/batches"),
    ("post", "/api/v1/youtube/batches"),
    ("get", f"/api/v1/youtube/batches/{_FAKE_ID}"),
    ("delete", f"/api/v1/youtube/batches/{_FAKE_ID}"),
    ("post", f"/api/v1/youtube/batches/{_FAKE_ID}/trigger"),
    ("post", f"/api/v1/youtube/batches/{_FAKE_ID}/finalize"),
    ("get", f"/api/v1/youtube/batches/{_FAKE_ID}/leads"),
    ("get", f"/api/v1/youtube/batches/{_FAKE_ID}/export"),
    ("get", "/api/v1/youtube/credits/today"),
]


@pytest.mark.parametrize("method,path", _YOUTUBE_ENDPOINTS)
async def test_youtube_endpoints_reject_invalid_token(
    client: AsyncClient, method: str, path: str
) -> None:
    r = await client.request(method, path, headers={"Authorization": "Bearer not-a-real-jwt"})
    assert r.status_code == 401, f"{method.upper()} {path} returned {r.status_code}, expected 401"


@pytest.mark.parametrize("method,path", _YOUTUBE_ENDPOINTS)
async def test_youtube_endpoints_reject_missing_token(
    client: AsyncClient, method: str, path: str
) -> None:
    r = await client.request(method, path)
    # HTTPBearer(auto_error=True) → 403 when the header is absent; get_current_user → 401.
    # Either way the request must not be authorized (and must never be 200).
    assert r.status_code in (401, 403), (
        f"{method.upper()} {path} returned {r.status_code}, expected 401/403"
    )
