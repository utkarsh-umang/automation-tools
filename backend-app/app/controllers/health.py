"""Health check controller."""

import asyncio

import httpx
from fastapi import APIRouter

from app.cache.redis_client import cache
from app.celery_app import celery_app
from app.core.config import config
from app.db.session import engine
from app.mongo.get_connection import get_database_connection
from app.schemas.common import HealthResponse

router = APIRouter()


async def _check_postgres() -> str:
    """Ping Postgres (async)."""
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(engine) as session:
            await session.execute(text("SELECT 1"))
        return "connected"
    except Exception:
        return "unreachable"


def _check_mongo() -> str:
    """Ping MongoDB."""
    try:
        db = get_database_connection()
        db.command("ping")
        return "connected"
    except Exception:
        return "unreachable"


def _check_redis() -> str:
    """Ping Redis."""
    try:
        if cache._available and cache._client:
            cache._client.ping()
            return "connected"
    except Exception:
        pass
    return "unreachable"


def _check_celery() -> str:
    """Ping Celery workers via broker (inspect)."""
    try:
        inspect = celery_app.control.inspect(timeout=1.0)
        if inspect is None:
            return "unreachable"
        ping = inspect.ping()
        if ping:
            return "connected"
        return "no_workers"
    except Exception:
        return "unreachable"


async def _check_flower() -> str:
    """HTTP check against Flower UI (local dev)."""
    try:
        base = config.FLOWER_URL.rstrip("/")
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{base}/")
            if response.status_code < 500:
                return "connected"
    except Exception:
        pass
    return "unreachable"


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check with per-service connectivity status.
    Returns 200 with status for Postgres, MongoDB, Redis, Celery workers, and Flower.
    """
    postgres_status = await _check_postgres()
    mongo_status = _check_mongo()
    redis_status = _check_redis()
    celery_status = await asyncio.to_thread(_check_celery)
    flower_status = await _check_flower()

    return HealthResponse(
        status="ok",
        environment=config.ENVIRONMENT,
        postgres=postgres_status,
        mongo=mongo_status,
        redis=redis_status,
        celery=celery_status,
        flower=flower_status,
    )
