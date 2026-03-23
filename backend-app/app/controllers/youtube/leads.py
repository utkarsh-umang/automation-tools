"""Routes: leads for a batch.

GET  /api/v1/youtube/batches/{batch_id}/leads    paginated, sorted by score
GET  /api/v1/youtube/batches/{batch_id}/export   stub — 501
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.repositories.youtube import batch_repo, lead_repo

router = APIRouter()


@router.get("/{batch_id}/leads")
def list_leads(
    batch_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200, alias="pageSize"),
) -> dict:
    """Return paginated leads for a batch, sorted by score descending."""
    batch = batch_repo.get_by_id(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    leads, total = lead_repo.paginated_list(batch_id, page=page, page_size=page_size)
    return {
        "leads": leads,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


@router.get("/{batch_id}/export")
def export_leads(batch_id: str) -> JSONResponse:
    """CSV export — not yet implemented."""
    return JSONResponse(
        status_code=501,
        content={"message": "CSV export coming soon"},
    )
