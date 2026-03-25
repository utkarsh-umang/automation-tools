"""Routes: leads for a batch.

GET  /api/v1/youtube/batches/{batch_id}/leads    paginated, sorted by score
GET  /api/v1/youtube/batches/{batch_id}/export   download all leads as CSV
"""

import csv
import io
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.repositories.youtube import batch_repo, lead_repo
from app.schemas.youtube.batch import BatchStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# Columns exported — all lead fields, in display order
_EXPORT_HEADERS = [
    "Channel Name",
    "Channel URL",
    "Channel ID",
    "Email",
    "Email Status",
    "Subscribers",
    "Uploads Last 30d",
    "Avg Views",
    "Score",
    "Country",
    "Last Upload",
    "Discovered At",
    "Search Term ID",
]


def _lead_to_row(lead: dict) -> list:
    """Map a lead document to an ordered export row matching _EXPORT_HEADERS."""
    def _fmt(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return str(value)

    return [
        _fmt(lead.get("channelName")),
        _fmt(lead.get("channelUrl")),
        _fmt(lead.get("channelId")),
        _fmt(lead.get("email")),
        _fmt(lead.get("emailStatus")),
        _fmt(lead.get("subscribers")),
        _fmt(lead.get("uploadsLast30d")),
        _fmt(lead.get("avgViews")),
        _fmt(lead.get("score")),
        _fmt(lead.get("country")),
        _fmt(lead.get("lastUpload")),
        _fmt(lead.get("discoveredAt")),
        _fmt(lead.get("searchTermId")),
    ]


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
def export_leads(batch_id: str) -> StreamingResponse:
    """Export all leads for a batch as a CSV file download."""
    batch = batch_repo.get_by_id(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.get("status") != BatchStatus.FINALIZED.value:
        raise HTTPException(
            status_code=400,
            detail="Batch must be finalized before exporting",
        )

    leads = lead_repo.get_all_for_batch(batch_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(_EXPORT_HEADERS)
    for lead in leads:
        writer.writerow(_lead_to_row(lead))

    batch_name = batch.get("name", batch_id)
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in batch_name).strip().replace(" ", "_")
    filename = f"leads_{safe_name}.csv"

    logger.info("Exported %d leads for batch %s as CSV", len(leads), batch_id)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
