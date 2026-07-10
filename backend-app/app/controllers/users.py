"""Users controller — admin-managed user creation."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, require_roles
from app.db.session import get_db_session
from app.models.user import UserRole
from app.schemas.auth import UserCreate, UserResponse
from app.services.user_service import count_users, create_user, get_user_by_id

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user's own profile (role included)",
)
async def get_me(
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserResponse:
    user = await get_user_by_id(db, uuid.UUID(current_user.id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.post(
    "/seed",
    response_model=UserResponse,
    summary="Bootstrap first ADMIN (only works when no users exist)",
)
async def seed_admin(body: UserCreate, db: AsyncSession = Depends(get_db_session)) -> UserResponse:
    """
    Create the very first ADMIN user when the users table is empty.
    This endpoint is unauthenticated intentionally — use it once from the
    FastAPI docs to bootstrap the system, then it will reject all subsequent calls.
    """
    if await count_users(db) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seed endpoint disabled: users already exist.",
        )
    body.role = UserRole.ADMIN
    user = await create_user(db, body)
    return UserResponse.model_validate(user)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (ADMIN only)",
)
async def create_new_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_roles("ADMIN")),
) -> UserResponse:
    """Create a user with any role. Requires ADMIN JWT."""
    user = await create_user(db, body)
    return UserResponse.model_validate(user)
