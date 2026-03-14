# Frontend

React + TypeScript + Vite frontend template. Single-app structure.

## Setup

From repo root:

```bash
task frontend:install
```

## Run

```bash
task frontend:run
```

Dev server: http://localhost:5173

## Generate API Client

Requires the backend to be running on port 8000. From repo root:

```bash
task backend:up   # in one terminal
task frontend:generate-client
```

The script fetches the spec from `http://127.0.0.1:8000/openapi.json` (not localhost, to avoid hitting another backend) and generates the client. Custom URL:

```bash
OPENAPI_URL=https://api.example.com/openapi.json task frontend:generate-client
```

## Environment

- `VITE_API_BASE_URL` — API base URL (default: `http://127.0.0.1:8000`). Create `frontend/.env` and set this if your backend runs elsewhere. The backend’s root `.env` must list the frontend origin in `CORS_ORIGINS` (e.g. `http://localhost:5173`).
- `OPENAPI_URL` — OpenAPI spec URL for codegen (default: `http://127.0.0.1:8000/openapi.json`)

## Jira Ticket

See [docs/TEMPLATE_APP_JIRA_TICKET.md](../docs/TEMPLATE_APP_JIRA_TICKET.md) for implementation stories.
