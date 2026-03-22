---
name: backend-api-design-auth
description: >-
  Documents the auth system built for this project and provides conventions for
  creating new authenticated API endpoints. Use when adding new routes,
  protecting endpoints with auth or roles, creating new services, or any time
  auth-related backend work is being done.
---

# Auth System — Design & Conventions

Auth is **fully implemented** in this project. Do not add new auth logic from scratch — extend what exists.

---

## What Was Built

| Layer | File | Purpose |
|-------|------|---------|
| Model | `app/models/user.py` | `User` table, `UserRole` enum |
| Schemas | `app/schemas/auth.py` | `UserCreate`, `UserLogin`, `Token`, `UserResponse` |
| Security | `app/core/security.py` | JWT sign/verify, password hash/verify |
| Auth dependency | `app/core/auth.py` | `get_current_user`, `require_roles`, `CurrentUser` |
| Service | `app/services/user_service.py` | `create_user`, `get_user_by_email`, `get_user_by_id`, `count_users` |
| Controllers | `app/controllers/auth.py` | `POST /api/v1/auth/login` |
| Controllers | `app/controllers/users.py` | `POST /api/v1/users/seed`, `POST /api/v1/users` |

### Roles

```python
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
```

No signup page exists. Users are **created only via the FastAPI docs** (`/docs`):
- First admin: `POST /api/v1/users/seed` (no auth required, only works when 0 users exist)
- All subsequent users: `POST /api/v1/users` (ADMIN Bearer token required)

### Token

- **Type:** Bearer JWT (python-jose, HS256)
- **Payload:** `{ "sub": "<user_id_uuid>", "exp": <timestamp> }`
- **Expiry:** 24 hours (`ACCESS_TOKEN_EXPIRE_MINUTES` in config)
- **Header:** `Authorization: Bearer <token>`

---

## Using Auth in New Endpoints

### Require any authenticated user

```python
from app.core.auth import CurrentUser, get_current_user

@router.get("/items")
async def list_items(
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
):
    # current_user.id    → str (UUID)
    # current_user.email → str
    # current_user.role  → UserRole ("ADMIN" | "MEMBER")
    ...
```

### Restrict to a specific role

```python
from app.core.auth import require_roles

@router.post("/admin-only-thing")
async def admin_action(
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_roles("ADMIN")),
):
    ...
```

Multiple roles (OR logic):
```python
Depends(require_roles("ADMIN", "MEMBER"))
```

### `CurrentUser` shape

```python
class CurrentUser(BaseModel):
    id: str          # UUID as string
    email: str
    role: UserRole   # UserRole.ADMIN or UserRole.MEMBER
    roles: list[str] # ["ADMIN"] or ["MEMBER"] — convenience list
```

---

## Adding a New Protected Resource

Follow this checklist when adding a new resource that needs auth:

1. **Model** — add SQLModel in `app/models/<resource>.py`, import in `app/models/__init__.py`
2. **Migration** — `task backend:revision` then `task backend:migrate`
3. **Schema** — add request/response Pydantic models in `app/schemas/<resource>.py`
4. **Service** — business logic in `app/services/<resource>_service.py`; keep controllers thin
5. **Controller** — FastAPI router in `app/controllers/<resource>.py`; add `Depends(get_current_user)` or `Depends(require_roles(...))` on routes that need protection
6. **Register** — add `api_v1_router.include_router(...)` in `app/controllers/__init__.py`
7. **Tests** — add integration tests in `tests/test_<resource>.py`; use `clean_db` autouse fixture for isolation

### Controller template (protected)

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import CurrentUser, get_current_user, require_roles
from app.db.session import get_db_session
from app.schemas.<resource> import <Resource>Create, <Resource>Response
from app.services.<resource>_service import create_<resource>

router = APIRouter()

@router.post("", response_model=<Resource>Response, status_code=status.HTTP_201_CREATED)
async def create(
    body: <Resource>Create,
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> <Resource>Response:
    item = await create_<resource>(db, body, owner_id=current_user.id)
    return <Resource>Response.model_validate(item)
```

---

## Error Codes Auth Returns

| Situation | HTTP status |
|-----------|-------------|
| Missing / malformed `Authorization` header | 403 |
| Invalid or expired JWT | 401 |
| Valid token but user deleted / inactive | 401 |
| Authenticated but wrong role | 403 |

---

## Frontend Integration

The frontend auth is in `frontend/src/`:

| File | Role |
|------|------|
| `context/AuthContext.tsx` | `AuthProvider` — `login(token, user?)`, `logout()`, `isAuthenticated`, `user` |
| `hooks/useAuth.ts` | `useAuth()` — consumes `AuthContext` |
| `utils/token.ts` | `getToken/setToken/removeToken` (localStorage), `decodeTokenPayload` |
| `components/ProtectedRoute.tsx` | Redirects to `/login` if not authenticated |

After login, `OpenAPI.TOKEN` is set on the generated client so all subsequent generated service calls send the Bearer token automatically. No manual header injection needed.

### Adding a new protected frontend page

1. Run `task frontend:generate-client` after adding the backend route
2. Create a hook in `src/hooks/api/use<Resource>Query.ts` wrapping the generated service with `useQuery` / `useMutation`
3. Wrap the route in `<ProtectedRoute>` in `src/App.tsx`
4. If the page is ADMIN-only, check `user.role === 'ADMIN'` from `useAuth()` and redirect or show a 403 view

---

## Key Config Values

```
SECRET_KEY               → JWT signing key (set in .env)
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  (24 h)
```

Change `SECRET_KEY` from the default `change-me-in-production` before going to production.
