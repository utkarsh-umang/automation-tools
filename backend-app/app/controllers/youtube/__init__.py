"""YouTube API controllers.

All YouTube routes require an ADMIN JWT (``require_roles("ADMIN")``), enforced
at the router level below. These endpoints expose scraped lead PII and can
spend the daily API quota, so they must not be reachable by MEMBER accounts —
MEMBER access is restricted to the thumbnail creator only.
"""

from fastapi import APIRouter, Depends

from app.controllers.youtube.batches import router as batches_router
from app.controllers.youtube.credits import router as credits_router
from app.controllers.youtube.leads import router as leads_router
from app.core.auth import require_roles

youtube_router = APIRouter(dependencies=[Depends(require_roles("ADMIN"))])
youtube_router.include_router(batches_router, prefix="/batches", tags=["youtube-batches"])
youtube_router.include_router(leads_router, prefix="/batches", tags=["youtube-leads"])
youtube_router.include_router(credits_router, prefix="/credits", tags=["youtube-credits"])
