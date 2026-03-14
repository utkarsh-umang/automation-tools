# FastAPI Backend

Production-ready FastAPI backend with dual database support (Postgres + MongoDB), Redis caching, and a clear layered architecture. Designed for the fullstack-template monorepo.

---

## Overview

| Store | Technology | Use for |
|-------|------------|---------|
| **Postgres** | SQLModel, asyncpg, Alembic | Users, auth, transactional data, relations, JOINs |
| **MongoDB** | PyMongo/Motor | Documents, JSON blobs, flexible schemas, logs |
| **Redis** | redis-py | Caching, sessions, rate limiting |

**Architecture:** Controllers (thin) → Services (logic) → DB / Mongo / Cache

---

## Monorepo Context

This backend lives in `backend-app/`. **All commands run from the repo root** using Task:

```bash
# From repo root
task dev:infra      # Start Postgres, MongoDB, Redis (Docker)
task backend:up     # Migrate + start uvicorn
```

Do not run `poetry` or `uvicorn` from inside `backend-app/` in normal workflows—use the Taskfile from root.

---

## Prerequisites

- Python 3.11+
- Task (taskfile.dev)
- Docker (for Postgres, MongoDB, Redis)
- Poetry (managed via Task)

---

## Environment Variables

The app loads config from the **repo root `.env`** (or `backend-app/local.env` as fallback). Create it with `task env:create` from root.

### App

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `local` | `local` / `uat` / `prod`. Affects MongoDB driver (sync vs async) and GCP secrets. |
| `SECRET_KEY` | `change-me-in-production` | **Change in production.** Used for signing, JWT, etc. |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins. JSON array or comma-separated. |
| `API_V1_STR` | `/api/v1` | API prefix. Versioned routes live under this path. |

### Postgres

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | Postgres host. Use service name in Docker prod (e.g. `postgres`). |
| `POSTGRES_PORT` | `5432` | Postgres port. |
| `POSTGRES_USER` | `postgres` | Database user. Must match `docker-compose` for local dev. |
| `POSTGRES_PASSWORD` | `postgres` | Database password. **Change in production.** |
| `POSTGRES_DB` | `myapp` | Database name. Must match `docker-compose` for local dev. |

### MongoDB

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_LOCAL_URI` | `mongodb://localhost:27017` | Local MongoDB URI. Use `mongodb://mongo:27017` if app runs in Docker. |
| `MONGO_PROD_URI` | _(none)_ | Prod URI (if not using GCP Secret Manager). |
| `MONGO_DB_NAME` | `myapp_docs` | Default database for documents. |
| `MONGO_TEST_DB_NAME` | `myapp_docs_test` | Database used when `is_test_write=True` (tests). |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis host. Use service name in Docker (e.g. `redis`). |
| `REDIS_PORT` | `6379` | Redis port. |
| `REDIS_PASSWORD` | _(none)_ | Redis password. Set in production if required. |

### GCP (optional, prod only)

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | _(none)_ | GCP project for Secret Manager. |
| `GCP_SECRET_NAME` | _(none)_ | Secret name containing MongoDB URI. When set, URI is fetched from GCP instead of env. |

### What to change

- **Local dev:** Defaults work with `task dev:infra` (Docker). No changes needed unless ports conflict.
- **Production:** Set `SECRET_KEY`, `POSTGRES_PASSWORD`, `CORS_ORIGINS`, `ENVIRONMENT=prod`, and DB/Redis hosts.
- **Port conflicts:** If 27017 is in use, change `MONGO_LOCAL_URI` (e.g. `mongodb://localhost:27018`) and update `docker-compose` MongoDB port mapping.

---

## Setup & Run

**First time:**

1. Create `.env` at repo root: `task env:create`
2. Edit `.env` if needed (defaults work with Docker)
3. Start infra: `task dev:infra`
4. Install deps: `task backend:install`
5. Start backend: `task backend:up`

**Daily:**

```bash
task dev:infra    # If not already running
task backend:up
```

- API: http://localhost:8000  
- Health: http://localhost:8000/health  
- Docs: http://localhost:8000/docs  

---

## Project Structure

```
backend-app/
├── app/
│   ├── core/              # Config, errors, auth contract
│   │   ├── config.py      # Pydantic Settings (loads .env)
│   │   ├── errors/        # Custom exceptions + handlers
│   │   └── auth.py        # get_current_user, require_roles (implement these)
│   ├── db/                # Postgres
│   │   ├── session.py     # AsyncSession, get_db_session
│   │   └── base.py        # Base model (id, created_at, updated_at)
│   ├── models/            # SQLModel ORM models (import here for Alembic)
│   ├── mongo/             # MongoDB
│   │   ├── connection_manager.py
│   │   ├── get_connection.py
│   │   ├── insert.py, read.py, delete.py, upsert.py
│   │   └── helpers.py
│   ├── cache/             # Redis
│   │   └── redis_client.py
│   ├── controllers/       # API routes (thin, delegate to services)
│   ├── schemas/           # Pydantic request/response models
│   ├── services/          # Business logic
│   └── utils/             # Helpers
├── migrations/            # Alembic (Postgres only)
├── main.py                # FastAPI app, routers, middleware
├── pyproject.toml
└── tests/
```

---

## Database Guide

| Use Postgres (SQLModel) for | Use MongoDB for |
|-----------------------------|-----------------|
| Users, auth, roles | Large/nested JSON documents |
| Orders, payments, transactions | File metadata, content blobs |
| Rigid schemas, relations | Flexible/evolving schemas |
| JOINs, SQL aggregations | Logs, analytics, audit trails |
| Config, feature flags | Caching-adjacent storage |

**Rule of thumb:** Spreadsheet → Postgres. JSON file → MongoDB.

---

## Extending the App

### Add a Postgres model

1. Create `app/models/your_model.py` inheriting from `app.db.base.Base`
2. Import it in `app/models/__init__.py`
3. Run `task backend:revision` or `poetry run alembic revision --autogenerate -m "add your_model"`
4. Run `task backend:migrate`

### Add a controller (API route)

1. Create `app/controllers/your_resource.py` with an `APIRouter`
2. Register in `app/controllers/__init__.py` or `main.py`

### Use MongoDB

```python
from app.mongo.insert import insert_document
from app.mongo.read import fetch_from_collection
from app.schemas.common import StatusOr

result = insert_document("documents", {"title": "My Doc", "content": {...}})
if result.success:
    doc_id = result.data["inserted_id"]
```

### Add auth

1. Implement `get_current_user` in `app/core/auth.py` (JWT, OAuth, etc.)
2. Return a `CurrentUser` (or subclass)
3. Use `Depends(get_current_user)` and `require_roles` in protected routes

The template raises `NotImplementedError` until you implement these.

---

## Commands (from repo root)

| Task | Description |
|------|-------------|
| `task dev:infra` | Start Postgres, MongoDB, Redis (Docker) |
| `task dev:down` | Stop Docker infra |
| `task backend:install` | Install Python deps (Poetry) |
| `task backend:up` | Migrate + start uvicorn |
| `task backend:migrate` | Run Alembic migrations |
| `task backend:revision` | Create new migration |
| `task backend:test` | Run pytest |
| `task backend:lint` | Ruff check |
| `task backend:format` | Ruff format |

---

## Testing

```bash
task backend:test
```

Tests use `tests/conftest.py` for fixtures. Health check tests run without real DBs; integration tests can use `MONGO_TEST_DB_NAME` and a test Postgres DB.

---

## Production

- **Infra:** Postgres, MongoDB, Redis as managed services or containers
- **App:** Run uvicorn in a container; or use Gunicorn + uvicorn workers
- **Env:** Set `ENVIRONMENT=prod`, strong `SECRET_KEY`, real DB URIs
- **GCP:** Optional—use Secret Manager for MongoDB URI when `GCP_PROJECT_ID` and `GCP_SECRET_NAME` are set
