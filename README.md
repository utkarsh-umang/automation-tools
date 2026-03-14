# fullstack-template

Monorepo: FastAPI backend + React TypeScript frontend. All commands run from the repo root via Task.

## Quick start

1. **Install Task** (if needed): https://taskfile.dev/installation

2. **Create `.env`**
   ```bash
   task env:create
   ```
   Then edit `.env` with your Postgres, MongoDB, Redis values.

3. **Start backend**
   ```bash
   task backend:up
   ```
   Runs migrations, then starts uvicorn. API: http://localhost:8000

## Task commands (run from root)

| Task | Description |
|------|-------------|
| `task env:create` | Create `.env` from `.env.example` |
| `task backend:install` | Install Python deps (Poetry) |
| `task backend:up` | Migrate + start uvicorn |
| `task backend:migrate` | Run Postgres migrations |
| `task backend:revision MESSAGE=add_users` | Create new Alembic migration |
| `task backend:test` | Run tests |
| `task backend:lint` | Lint (ruff) |
| `task backend:format` | Format (ruff) |

## Project layout

```
.
├── .env              # Your secrets (create from .env.example)
├── .env.example      # Env template
├── Taskfile.yml      # Root task runner
├── backend-app/      # FastAPI backend
└── frontend/         # React frontend
```
