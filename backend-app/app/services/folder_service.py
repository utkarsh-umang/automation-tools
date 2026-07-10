"""Thumbnail folders business logic — shared org-wide client style folders."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import folder_repo
from app.schemas.folders import FolderListResponse, FolderPublic


async def create_folder(
    session: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    style_prompt: str,
) -> FolderPublic:
    folder_id = uuid.uuid4()
    folder = await folder_repo.create_folder(session, folder_id, name, style_prompt, user_id)
    return FolderPublic.model_validate(folder)


async def list_folders(session: AsyncSession) -> FolderListResponse:
    """Shared org-wide: every authenticated user sees every folder."""
    folders = await folder_repo.list_folders(session)
    return FolderListResponse(folders=[FolderPublic.model_validate(f) for f in folders])


async def update_folder(
    session: AsyncSession,
    folder_id: uuid.UUID,
    name: str | None,
    style_prompt: str | None,
) -> FolderPublic:
    existing = await folder_repo.get_folder(session, folder_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    updated = await folder_repo.update_folder(
        session, folder_id, name=name, style_prompt=style_prompt
    )
    return FolderPublic.model_validate(updated)
