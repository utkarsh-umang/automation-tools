"""PostgreSQL access for ``thumbnail_folders`` (shared org-wide client style folders)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.thumbnail_folder import ThumbnailFolder


def _folder_to_dict(folder: ThumbnailFolder) -> dict[str, Any]:
    return {
        "id": folder.id,
        "name": folder.name,
        "style_prompt": folder.style_prompt,
        "created_by": folder.created_by,
        "created_at": folder.created_at,
        "updated_at": folder.updated_at,
    }


async def create_folder(
    session: AsyncSession,
    folder_id: uuid.UUID,
    name: str,
    style_prompt: str,
    created_by: uuid.UUID,
) -> dict[str, Any]:
    folder = ThumbnailFolder(
        id=folder_id, name=name, style_prompt=style_prompt, created_by=created_by
    )
    session.add(folder)
    await session.flush()
    await session.refresh(folder)
    return _folder_to_dict(folder)


async def get_folder(
    session: AsyncSession, folder_id: uuid.UUID
) -> dict[str, Any] | None:
    row = await session.get(ThumbnailFolder, folder_id)
    return _folder_to_dict(row) if row else None


async def list_folders(session: AsyncSession) -> list[dict[str, Any]]:
    """Shared org-wide: every folder, regardless of who created it."""
    stmt = select(ThumbnailFolder).order_by(ThumbnailFolder.name.asc())
    result = await session.execute(stmt)
    return [_folder_to_dict(r) for r in result.scalars().all()]


async def update_folder(
    session: AsyncSession,
    folder_id: uuid.UUID,
    *,
    name: str | None,
    style_prompt: str | None,
) -> dict[str, Any] | None:
    values: dict[str, Any] = {"updated_at": func.now()}
    if name is not None:
        values["name"] = name
    if style_prompt is not None:
        values["style_prompt"] = style_prompt
    await session.execute(
        update(ThumbnailFolder).where(ThumbnailFolder.id == folder_id).values(**values)
    )
    return await get_folder(session, folder_id)
