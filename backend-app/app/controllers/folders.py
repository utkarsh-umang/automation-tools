"""Thumbnail folders controller — shared org-wide client style folders.

Any authenticated user (ADMIN or MEMBER) can create, list, and edit folders;
they're shared across the whole team so a client's preferred style travels
with the client, not with whichever employee first set it up.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db_session
from app.schemas.folders import (
    FolderCreate,
    FolderListResponse,
    FolderPublic,
    FolderSummaryResponse,
    FolderUpdate,
)
from app.services import folder_service, thumbnail_service

router = APIRouter()


@router.post("", response_model=FolderPublic)
async def create_folder(
    body: FolderCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FolderPublic:
    return await folder_service.create_folder(
        db, uuid.UUID(current_user.id), body.name, body.style_prompt
    )


@router.get("", response_model=FolderListResponse)
async def list_folders(
    _: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FolderListResponse:
    return await folder_service.list_folders(db)


@router.get("/summary", response_model=FolderSummaryResponse)
async def folder_summaries(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FolderSummaryResponse:
    """Per-folder thumbnail count + cover image for the album grid.

    ADMIN counts every member's thumbnails; MEMBER only their own. The
    unfoldered bucket comes back with ``folder_id = null``.
    """
    return await thumbnail_service.get_folder_summaries(
        db, uuid.UUID(current_user.id), is_admin=current_user.role == "ADMIN"
    )


@router.patch("/{folder_id}", response_model=FolderPublic)
async def update_folder(
    folder_id: uuid.UUID,
    body: FolderUpdate,
    _: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FolderPublic:
    return await folder_service.update_folder(db, folder_id, body.name, body.style_prompt)
