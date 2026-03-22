"""Auth dependency — get_current_user and require_roles."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.user import UserRole

_bearer = HTTPBearer()


class CurrentUser(BaseModel):
    id: str
    email: str
    role: UserRole
    roles: list[str] = []

    model_config = {"from_attributes": True}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    """FastAPI dependency — validates Bearer JWT and returns the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Lazy import to avoid circular dependency at module load time
    from app.services.user_service import get_user_by_id

    user = await get_user_by_id(db, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception

    return CurrentUser(
        id=str(user.id),
        email=user.email,
        role=user.role,
        roles=[user.role.value],
    )


def require_roles(*roles: str):
    """Dependency factory for role-based access control."""

    async def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check
