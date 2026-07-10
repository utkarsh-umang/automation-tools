"""API controllers (thin, delegate to services)."""

from fastapi import APIRouter

from app.controllers.auth import router as auth_router
from app.controllers.folders import router as folders_router
from app.controllers.thumbnail_creator import thumbnail_creator_router as thumbnails_router
from app.controllers.users import router as users_router
from app.controllers.youtube import youtube_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(users_router, prefix="/users", tags=["users"])
api_v1_router.include_router(thumbnails_router, prefix="/thumbnails", tags=["thumbnails"])
api_v1_router.include_router(folders_router, prefix="/folders", tags=["folders"])
api_v1_router.include_router(youtube_router, prefix="/youtube")
