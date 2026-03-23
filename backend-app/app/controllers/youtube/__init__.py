"""YouTube API controllers."""

from fastapi import APIRouter

from app.controllers.youtube.batches import router as batches_router
from app.controllers.youtube.credits import router as credits_router
from app.controllers.youtube.leads import router as leads_router

youtube_router = APIRouter()
youtube_router.include_router(batches_router, prefix="/batches", tags=["youtube-batches"])
youtube_router.include_router(leads_router, prefix="/batches", tags=["youtube-leads"])
youtube_router.include_router(credits_router, prefix="/credits", tags=["youtube-credits"])
