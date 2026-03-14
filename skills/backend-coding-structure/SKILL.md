# AI Context: FastAPI Backend Structure

## Structure

```
backend-app/
├── app/
│   ├── core/           # Config, errors, auth stub
│   ├── db/             # Postgres (SQLModel) — session, base
│   ├── models/         # SQLModel ORM models (import here for Alembic)
│   ├── mongo/          # MongoDB — connection, CRUD (insert, read, delete, upsert)
│   ├── cache/          # Redis
│   ├── controllers/    # API endpoints (thin, delegate to services)
│   ├── schemas/        # Pydantic request/response models
│   ├── services/       # Business logic
│   └── utils/          # Helpers
├── migrations/         # Alembic (Postgres only)
├── main.py
├── alembic.ini
├── pyproject.toml
├── local.env.example
└── tests/
```

## Database Decision Guide

| Use **Postgres (SQLModel)** for | Use **MongoDB** for |
|---|---|
| Users, auth, roles, permissions | Large/nested JSON documents |
| Transactional data (orders, payments) | File metadata, content blobs |
| Rigid schemas and relations | Flexible/evolving schemas |
| Anything you'd JOIN or aggregate in SQL | Logs, analytics events, audit trails |
| Config tables, feature flags | Caching-adjacent document storage |

**Rule of thumb:** Spreadsheet → Postgres. JSON file → MongoDB.

## Auth Contract

`app/core/auth.py` defines `get_current_user`, `require_roles`, and `CurrentUser` as interfaces. They raise `NotImplementedError` by default. The consuming app **must** implement these before using auth-protected routes. Do not add auth logic to the template itself.

## Layering Rules

- **Controllers** → **services** → **db** (Postgres) / **mongo** (MongoDB) / **cache** (Redis)
- Controllers are thin; services hold business logic.

## Conventions

- **Postgres:** SQLModel models in `models/`, sessions via `Depends(get_db_session)`, Alembic migrations for schema changes.
- **MongoDB:** Use `StatusOr` for all operations, connections via `get_database_connection()`.
- **Validation:** Pydantic schemas in `schemas/`.
- Prefer async where applicable.

## How to Add

| Task | Where |
|------|-------|
| New Postgres model | `app/models/` + import in `__init__.py`, then `alembic revision --autogenerate -m "add X"` |
| New MongoDB collection | Use `app/mongo/insert.py`, `read.py`, etc. with collection name |
| New endpoint | `app/controllers/`, register in `app/controllers/__init__.py` and/or `main.py` |
| New schema | `app/schemas/` |

## Commands

- Run: `poetry run uvicorn main:app --reload`
- Test: `poetry run pytest`
- Lint: `poetry run ruff check app`
- Migrate: `poetry run alembic revision --autogenerate -m "message"`
- Upgrade: `poetry run alembic upgrade head`
