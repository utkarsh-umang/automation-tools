# fullstack-template — context for agents

Monorepo: **FastAPI** backend (`backend-app/`) and **React + TypeScript + Vite** frontend (`frontend/`). Commands run from the **repo root** via [Task](https://taskfile.dev) (`Taskfile.yml`). Local infra (Postgres, MongoDB, Redis) is **Docker** (`docker-compose.yml`). Env: create with `task env:create` from root; backend reads the root `.env`.

---

## Repository layout

```
.
├── .env / .env.example     # App secrets and config (root)
├── Taskfile.yml            # task dev:infra, backend:*, frontend:*
├── docker-compose.yml      # Postgres, MongoDB, Redis for local dev
├── backend-app/            # FastAPI application
├── frontend/               # Vite + React SPA
└── skills/                 # Agent skills and this file (CLAUDE.md)
```

---

## Backend (`backend-app/`)

### Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, Uvicorn |
| Config | Pydantic Settings (`app/core/config.py`), loads root `.env` |
| Relational DB | **Postgres** — SQLModel, asyncpg, **Alembic** migrations |
| Documents | **MongoDB** — PyMongo / Motor (`app/mongo/`) |
| Cache | **Redis** (`app/cache/redis_client.py`) |
| HTTP tests | pytest, pytest-asyncio, httpx |

Optional: GCP Secret Manager for Mongo URI in prod (Poetry extra `gcp`).

### Architecture

Thin **controllers** (`app/controllers/`) → **services** (`app/services/`) → **Postgres** (`app/db/`, `app/models/`), **Mongo** (`app/mongo/`), or **Redis** (`app/cache/`).

- **Entry:** `main.py` — FastAPI app, CORS, request-ID middleware, exception handlers.
- **Routes:** `/health` (health router); versioned API under `API_V1_STR` (default `/api/v1`) via `api_v1_router` in `app/controllers/__init__.py` — add new routers there.
- **Core:** `app/core/` — config, `auth.py` (contract for `get_current_user` / roles), `errors/` (handlers).
- **Schemas:** Pydantic models in `app/schemas/`.
- **Migrations:** `backend-app/migrations/` (Postgres only).

### Typical commands (from repo root)

`task dev:infra`, `task backend:install`, `task backend:up` (migrate + uvicorn), `task backend:test`, `task backend:migrate`.

---

## Frontend (`frontend/`)

### Stack

| Area | Technology |
|------|------------|
| Build | Vite, TypeScript |
| UI | React 19, Tailwind CSS 4 |
| Routing | react-router-dom |
| API | **OpenAPI-generated** TypeScript client (`src/client/`) using **axios** (`openapi-typescript-codegen`) |
| Server state | **TanStack React Query** (`@tanstack/react-query`) |

Regenerate the client after API changes: `task frontend:generate-client` (backend must expose `/openapi.json`; default fetch URL is configurable via `OPENAPI_URL`).

### API base URL

`src/config/api.ts` exports `apiBaseUrl` from `import.meta.env.VITE_API_BASE_URL`, defaulting to `http://127.0.0.1:8000`. `src/main.tsx` sets `OpenAPI.BASE = apiBaseUrl` so generated services call the correct host. Backend `CORS_ORIGINS` must include the Vite dev origin (e.g. `http://localhost:5173`).

### React Query usage

- **Provider:** `QueryClientProvider` wraps the app in `main.tsx`, with a shared `QueryClient` (`defaultOptions.queries`: `retry: 1`, `staleTime: 30_000`).
- **Pattern:** Custom hooks under `src/hooks/api/` wrap `useQuery` / `useMutation` and call **generated** service classes from `@/client` (e.g. `HealthService.healthHealthGet()`), not raw `fetch`.
- **Keys:** Stable `queryKey` arrays per resource (e.g. `['health']` for the health check).
- **Example:** `useHealthQuery` uses `queryFn: () => HealthService.healthHealthGet()`; pages (e.g. `Home`) consume `data`, `isLoading`, and `error` from that hook.

New features: add or regenerate client services, then add a small hook that ties React Query to the appropriate `*Service` method.

---

## Skills folder

`skills/backend-coding-structure/SKILL.md` and related files document backend conventions; this `CLAUDE.md` summarizes repo-wide structure and frontend–backend integration.
