"""Repository for yt_job_logs collection."""

from datetime import datetime

from app.mongo.insert import insert_document
from app.schemas.youtube.job_log import JobLogDocument

COLLECTION = "yt_job_logs"


def append(
    batch_id: str,
    event: str,
    message: str,
    search_term_id: str | None = None,
) -> None:
    """Insert a new log entry."""
    doc = JobLogDocument(
        batchId=batch_id,
        searchTermId=search_term_id,
        event=event,
        message=message,
        timestamp=datetime.utcnow(),
    )
    insert_document(COLLECTION, doc.model_dump(exclude={"id"}))
