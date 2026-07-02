"""FastAPI application entry point."""

import app.bootstrap_env  # noqa: F401 - side effect: load .env into os.environ
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import api_v1_router
from app.controllers.health import router as health_router
from app.core.config import config
from app.core.errors.exceptions import register_exception_handlers


def add_request_id_middleware(app: FastAPI) -> None:
    """Add request-ID middleware."""

    @app.middleware("http")
    async def _request_id(request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        return response

    return None  # type: ignore


# In production, don't expose the interactive API docs / OpenAPI schema — they
# hand out a complete, labeled map of every endpoint (P1-4).
_NON_PROD = {"local", "dev", "development", "test", "testing", "ci"}
_IS_PROD = config.ENVIRONMENT.lower() not in _NON_PROD

app = FastAPI(
    title="FastAPI Backend",
    version="0.1.0",
    openapi_url=None if _IS_PROD else "/openapi.json",
    docs_url=None if _IS_PROD else "/docs",
    redoc_url=None if _IS_PROD else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    # Scoped instead of wildcard (P1-8). The SPA is same-origin via nginx, so
    # this is defense-in-depth; wildcard + credentials is also invalid per spec.
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

add_request_id_middleware(app)
register_exception_handlers(app)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(api_v1_router, prefix=config.API_V1_STR)
