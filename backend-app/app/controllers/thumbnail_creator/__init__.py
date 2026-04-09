"""Thumbnail Creator API controllers."""

from fastapi import APIRouter

from app.controllers.thumbnail_creator.thumbnails import router as thumbnails_router

thumbnail_creator_router = APIRouter()
thumbnail_creator_router.include_router(thumbnails_router, prefix="/thumbnail", tags=["thumbnail-creator"])
