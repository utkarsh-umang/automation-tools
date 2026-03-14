# FastAPI Backend

Minimal production-ready FastAPI backend with dual database support (Postgres + MongoDB), Redis caching, and layered architecture.

## Overview

- **Postgres** (SQLModel): structured/relational data, users, auth, transactions
- **MongoDB** (Motor/PyMongo): documents, JSON blobs, flexible schemas
- **Redis**: caching

## Prerequisites

- Python 3.11+
- Postgres
- MongoDB
- Redis

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Copy env template and fill in values:
   ```bash
   cp local.env.example local.env
   ```

3. Start Postgres, MongoDB, and Redis.

4. Run migrations:
   ```bash
   poetry run alembic upgrade head
   ```

## Run

```bash
poetry run uvicorn main:app --reload
```

API: http://localhost:8000  
Health: http://localhost:8000/health  
Docs: http://localhost:8000/docs

## Test

```bash
poetry run pytest
```

## Project Structure

- `app/core/` — config, errors, auth stub
- `app/db/` — Postgres (SQLModel) session and base
- `app/models/` — SQLModel ORM models
- `app/mongo/` — MongoDB connection and CRUD
- `app/cache/` — Redis client
- `app/controllers/` — API endpoints
- `app/schemas/` — Pydantic models
- `app/services/` — business logic

## Database Guide

- **Postgres:** Users, auth, orders, anything relational or with JOINs.
- **MongoDB:** Large JSON docs, logs, flexible schemas, content blobs.

## Extending

1. Add SQLModel models in `app/models/`, run `alembic revision --autogenerate -m "add X"`.
2. Add MongoDB usage via `app/mongo/insert`, `read`, `delete`, `upsert`.
3. Implement `get_current_user` in `app/core/auth.py` for protected routes.
4. Add controllers and wire in `main.py` or `app/controllers/__init__.py`.
