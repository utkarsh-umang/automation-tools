"""User table model."""

import uuid
from enum import Enum

from sqlmodel import Field

from app.db.base import Base


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class User(Base, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.MEMBER)
    is_active: bool = Field(default=True)

    # Override id to ensure UUID default
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
