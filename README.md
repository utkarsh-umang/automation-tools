# fullstack-template

Monorepo: FastAPI backend + React TypeScript frontend. All commands run from the repo root via Task.

## Quick start

1. **Install Task** (if needed): https://taskfile.dev/installation
2. **Install Docker** (for Postgres, MongoDB, Redis)

3. **Create `.env`**
   ```bash
   task env:create
   ```
   Edit `.env` if needed (defaults work with Docker infra).

4. **Start infra + backend**
   ```bash
   task dev:infra    # Start Postgres, MongoDB, Redis (Docker)
   task backend:up   # Migrate + start uvicorn
   ```
   API: http://localhost:8000

5. **Frontend (optional)**
   ```bash
   task frontend:install
   task frontend:run
   ```
   Dev server: http://localhost:5173. Add `http://localhost:5173` to `CORS_ORIGINS` in `.env` for local dev.

## Task commands (run from root)

| Task | Description |
|------|-------------|
| `task dev:infra` | Start Postgres, MongoDB, Redis (Docker) |
| `task dev:down` | Stop Docker infra |
| `task env:create` | Create `.env` from `.env.example` |
| `task backend:install` | Install Python deps (Poetry) |
| `task backend:up` | Migrate + start uvicorn |
| `task backend:migrate` | Run Postgres migrations |
| `task backend:revision` | Create new Alembic migration |
| `task backend:test` | Run tests |
| `task backend:lint` | Lint (ruff) |
| `task backend:format` | Format (ruff) |
| `task frontend:install` | Install frontend deps (npm) |
| `task frontend:run` | Start Vite dev server |
| `task frontend:generate-client` | Generate API client from OpenAPI (requires backend) |

## Project layout

```
.
├── .env                 # Your secrets (create from .env.example)
├── .env.example         # Env template
├── Taskfile.yml         # Root task runner
├── docker-compose.yml   # Local infra (Postgres, MongoDB, Redis)
├── backend-app/         # FastAPI backend
└── frontend/            # React frontend
```

## Local dev flow

- **Infra:** Docker (Postgres, MongoDB, Redis) — `task dev:infra`
- **App:** uvicorn on host (hot reload) — `task backend:up`
- **Prod:** Everything containerized (app + infra)
