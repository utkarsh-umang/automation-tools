"""Auth endpoint tests."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_seed_creates_first_admin(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/users/seed",
        json={"email": "admin@test.com", "password": "secret123", "role": "MEMBER"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@test.com"
    # Seed always creates ADMIN regardless of requested role
    assert data["role"] == "ADMIN"


async def test_seed_rejected_when_users_exist(client: AsyncClient) -> None:
    # First seed succeeds
    await client.post(
        "/api/v1/users/seed",
        json={"email": "admin2@test.com", "password": "secret123"},
    )
    # Second seed must fail
    resp = await client.post(
        "/api/v1/users/seed",
        json={"email": "other@test.com", "password": "secret123"},
    )
    assert resp.status_code == 409


async def test_login_returns_token(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users/seed",
        json={"email": "login@test.com", "password": "mypassword"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@test.com", "password": "mypassword"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users/seed",
        json={"email": "bad@test.com", "password": "correct"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "bad@test.com", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_unknown_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "any"},
    )
    assert resp.status_code == 401


async def test_create_user_requires_admin_token(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/users",
        json={"email": "member@test.com", "password": "pass", "role": "MEMBER"},
    )
    # No token → 403 (HTTPBearer returns 403 when header is missing)
    assert resp.status_code in (401, 403)


async def test_admin_can_create_user(client: AsyncClient) -> None:
    # Bootstrap
    await client.post(
        "/api/v1/users/seed",
        json={"email": "adm@test.com", "password": "adminpass"},
    )
    token_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "adm@test.com", "password": "adminpass"},
    )
    token = token_resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/users",
        json={"email": "newmember@test.com", "password": "pass", "role": "MEMBER"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "newmember@test.com"
    assert resp.json()["role"] == "MEMBER"
