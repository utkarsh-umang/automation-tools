"""Shared test fixtures."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import config
from app.db.session import engine as app_engine
from main import app

# Separate engine with NullPool so cleanup never shares connections with the app pool
_cleanup_engine = create_async_engine(config.DATABASE_URL, poolclass=NullPool)
_cleanup_session = async_sessionmaker(bind=_cleanup_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncClient:
    """FastAPI async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def clean_db() -> None:
    """Truncate mutable tables before every test and reset the connection pool."""
    # Dispose the app's pool so stale event-loop-bound connections are cleared
    await app_engine.dispose()
    async with _cleanup_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        await session.commit()
    await asyncio.sleep(0)
    yield
