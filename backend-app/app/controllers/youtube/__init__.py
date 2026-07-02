"""YouTube API controllers.

All YouTube routes require a valid JWT (``get_current_user``), enforced at the
router level below — the same auth the thumbnail routes use. These endpoints
expose scraped lead PII and can spend the daily API quota, so they must not be
publicly reachable.
"""

from fastapi import APIRouter, Depends

from app.controllers.youtube.batches import router as batches_router
from app.controllers.youtube.credits import router as credits_router
from app.controllers.youtube.leads import router as leads_router
from app.core.auth import get_current_user

youtube_router = APIRouter(dependencies=[Depends(get_current_user)])
youtube_router.include_router(batches_router, prefix="/batches", tags=["youtube-batches"])
youtube_router.include_router(leads_router, prefix="/batches", tags=["youtube-leads"])
youtube_router.include_router(credits_router, prefix="/credits", tags=["youtube-credits"])
