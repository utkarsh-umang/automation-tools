"""Routes: batch CRUD and trigger.

GET    /api/v1/youtube/batches
POST   /api/v1/youtube/batches
GET    /api/v1/youtube/batches/{batch_id}
POST   /api/v1/youtube/batches/{batch_id}/trigger
POST   /api/v1/youtube/batches/{batch_id}/terms/{term_id}/reset-to-pending
DELETE /api/v1/youtube/batches/{batch_id}
"""

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, model_validator

from app.repositories.youtube import (
    batch_repo,
    daily_usage_repo,
    lead_repo,
    search_term_repo,
)
from app.schemas.youtube.batch import BatchFilters, BatchStatus
from app.schemas.youtube.search_term import TermStatus
from app.worker.orchestrator import run_batch

router = APIRouter()


# ── Request / response schemas ─────────────────────────────────────────────


class BatchFiltersCreate(BaseModel):
    minSubs: int = 0
    maxSubs: int = 1_000_000
    minUploadsLast30d: int = 1
    minAvgViews: int = 0
    excludeCountries: list[str] = ["IN"]
    region: str = "US"

    @model_validator(mode="after")
    def validate_sub_range(self) -> "BatchFiltersCreate":
        if self.maxSubs <= self.minSubs:
            raise ValueError("maxSubs must be greater than minSubs")
        if self.minSubs < 0:
            raise ValueError("minSubs must be >= 0")
        if self.minUploadsLast30d < 1:
            raise ValueError("minUploadsLast30d must be >= 1")
        if self.minAvgViews < 0:
            raise ValueError("minAvgViews must be >= 0")
        return self


class ResetTermToPendingResponse(BaseModel):
    message: str
    batchId: str
    termId: str
    leadsRemoved: int
    dispatched: bool
    dispatchBlockedReason: str | None = None


class BatchCreateRequest(BaseModel):
    name: str
    keyword: str
    terms: str  # raw string: '"term one", "term two"'
    filters: BatchFiltersCreate

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

    @field_validator("keyword")
    @classmethod
    def keyword_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("keyword must not be empty")
        return v.strip()

    @field_validator("terms")
    @classmethod
    def parse_terms(cls, v: str) -> str:
        """Validate that terms is a non-empty string; actual parsing happens in the route."""
        if not v.strip():
            raise ValueError("terms must not be empty")
        return v.strip()


def _parse_terms(raw: str) -> list[str]:
    """Parse a raw comma-separated quoted string into a list of terms.

    Accepts: '"term one", "term two"'
    Returns: ['term one', 'term two']
    Raises ValueError if format is invalid or any term is empty.
    """
    matches = re.findall(r'"([^"]*)"', raw)
    if not matches:
        raise ValueError(
            'terms must contain at least one term wrapped in double quotes, e.g. "term one", "term two"'
        )
    parsed = [t.strip() for t in matches]
    if any(t == "" for t in parsed):
        raise ValueError("each term must be non-empty after unquoting")
    return parsed


def _finalize_terms_must_all_be_done(batch_id: str) -> None:
    """Raise HTTPException 400 if any term is not successfully completed."""
    terms = search_term_repo.get_all_for_batch(batch_id)
    not_done = [t for t in terms if t.get("status") != TermStatus.DONE.value]
    if not not_done:
        return
    counts: dict[str, int] = {}
    for t in not_done:
        st = t.get("status", "unknown")
        counts[st] = counts.get(st, 0) + 1
    parts = [f"{k}: {v}" for k, v in sorted(counts.items())]
    raise HTTPException(
        status_code=400,
        detail=(
            "All search terms must succeed (status 'done') before finalizing. "
            f"Outstanding terms by status — {', '.join(parts)}"
        ),
    )


def _dispatch_batch_run_checks(batch_id: str, batch: dict) -> tuple[bool, str | None]:
    """Return (can_dispatch, error_message) without raising."""
    usage = daily_usage_repo.get_or_create_today()
    active_id = usage.get("activeBatchId")
    if active_id and active_id != batch_id:
        active_batch = batch_repo.get_by_id(active_id)
        active_name = active_batch.get("name", active_id) if active_batch else active_id
        return (
            False,
            f"Another batch is already running today: '{active_name}' ({active_id})",
        )

    status = batch.get("status")
    if status == BatchStatus.RUNNING.value:
        return False, "Batch is already running"
    if status == BatchStatus.COMPLETED.value:
        return False, "Batch is already completed"
    if status not in (BatchStatus.QUEUED.value, BatchStatus.PAUSED.value):
        return False, f"Batch cannot be triggered from status '{status}'"
    return True, None


# ── Routes ─────────────────────────────────────────────────────────────────


@router.get("")
def list_batches() -> list[dict]:
    """List all batches with progress."""
    return batch_repo.list_all()


@router.post("", status_code=201)
def create_batch(body: BatchCreateRequest) -> dict:
    """Create a new batch in queued state."""
    try:
        terms = _parse_terms(body.terms)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filters = BatchFilters(
        minSubs=body.filters.minSubs,
        maxSubs=body.filters.maxSubs,
        minUploadsLast30d=body.filters.minUploadsLast30d,
        minAvgViews=body.filters.minAvgViews,
        excludeCountries=body.filters.excludeCountries,
        region=body.filters.region,
    )
    batch_id = batch_repo.create(
        name=body.name,
        keyword=body.keyword,
        filters=filters,
        total_terms=len(terms),
    )
    search_term_repo.create_many(batch_id, terms)
    batch = batch_repo.get_by_id(batch_id)
    return batch


@router.get("/{batch_id}")
def get_batch(batch_id: str) -> dict:
    """Batch detail including full term list."""
    batch = batch_repo.get_by_id(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    terms = search_term_repo.get_all_for_batch(batch_id)
    return {**batch, "terms": terms}


@router.post("/{batch_id}/trigger", status_code=202)
def trigger_batch(batch_id: str) -> dict:
    """Start today's run for a batch.

    Returns 400 if another batch is already running today, or if the
    batch is not in a triggerable state.
    Returns 202 Accepted immediately; processing happens in Celery.
    """
    batch = batch_repo.get_by_id(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    ok, err = _dispatch_batch_run_checks(batch_id, batch)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    run_batch.delay(batch_id)
    return {"message": "Batch run dispatched", "batchId": batch_id}


@router.post("/{batch_id}/finalize")
def finalize_batch(batch_id: str) -> dict:
    """Deduplicate leads and mark batch as finalized."""
    batch = batch_repo.get_by_id(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    status = batch.get("status")
    if status == BatchStatus.FINALIZED.value:
        raise HTTPException(status_code=400, detail="Batch is already finalized")
    if status != BatchStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail="Batch must be fully processed before finalizing",
        )

    _finalize_terms_must_all_be_done(batch_id)

    removed = lead_repo.deduplicate_for_batch(batch_id)
    batch_repo.update_status(batch_id, BatchStatus.FINALIZED)
    return {"message": "Batch finalized", "duplicatesRemoved": removed}


@router.post("/{batch_id}/terms/{term_id}/reset-to-pending")
def reset_term_to_pending(batch_id: str, term_id: str) -> ResetTermToPendingResponse:
    """Clear a failed or running term back to pending, remove its leads, re-queue batch, try to dispatch."""
    batch = batch_repo.get_by_id(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    term = search_term_repo.get_by_id(term_id)
    if term is None:
        raise HTTPException(status_code=404, detail="Search term not found")

    if str(term.get("batchId")) != batch_id:
        raise HTTPException(status_code=400, detail="Term does not belong to this batch")

    t_status = term.get("status")
    if t_status == TermStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Term is already pending")

    if t_status not in (TermStatus.FAILED.value, TermStatus.RUNNING.value):
        raise HTTPException(
            status_code=400,
            detail=f"Can only reset terms that are failed or running; current status is '{t_status}'",
        )

    batch_status = batch.get("status")
    if batch_status == BatchStatus.RUNNING.value:
        raise HTTPException(
            status_code=409,
            detail="Cannot reset a term while a batch run is in progress",
        )

    leads_removed = lead_repo.delete_for_batch_term(batch_id, term_id)

    search_term_repo.reset_to_pending(term_id)

    if batch_status in (
        BatchStatus.FINALIZED.value,
        BatchStatus.COMPLETED.value,
        BatchStatus.FAILED.value,
    ):
        batch_repo.update_status(
            batch_id,
            BatchStatus.QUEUED,
            clear_completed_at=True,
        )

    batch_after = batch_repo.get_by_id(batch_id)
    assert batch_after is not None
    can_dispatch, dispatch_err = _dispatch_batch_run_checks(batch_id, batch_after)
    if can_dispatch:
        run_batch.delay(batch_id)
        return ResetTermToPendingResponse(
            message="Term reset to pending and batch run dispatched",
            batchId=batch_id,
            termId=term_id,
            leadsRemoved=leads_removed,
            dispatched=True,
            dispatchBlockedReason=None,
        )

    return ResetTermToPendingResponse(
        message=(
            "Term reset to pending. Start the batch manually when ready (Trigger)."
            if dispatch_err
            else "Term reset to pending"
        ),
        batchId=batch_id,
        termId=term_id,
        leadsRemoved=leads_removed,
        dispatched=False,
        dispatchBlockedReason=dispatch_err,
    )


@router.delete("/{batch_id}", status_code=204)
def delete_batch(batch_id: str) -> None:
    """Hard-delete a batch and all its associated terms and leads."""
    batch = batch_repo.get_by_id(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    lead_repo.delete_for_batch(batch_id)
    search_term_repo.delete_for_batch(batch_id)
    batch_repo.delete(batch_id)
