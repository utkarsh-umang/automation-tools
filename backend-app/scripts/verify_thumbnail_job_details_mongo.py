#!/usr/bin/env python3
"""Manual check: Mongo ``thumbnail_job_details`` insert, find, unique index.

Requires Mongo reachable at ``MONGO_LOCAL_URI`` (or default from config).
From ``backend-app``::

    poetry run python scripts/verify_thumbnail_job_details_mongo.py

Uses the test database name so it does not clobber primary dev data.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# Repo root (automation-tools) and backend-app on path
_BACKEND = Path(__file__).resolve().parents[1]
_ROOT = _BACKEND.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")
load_dotenv(_BACKEND / "local.env", override=True)

from pymongo.errors import DuplicateKeyError

from app.core.config import config
from app.repositories import mongo_repo


def main() -> None:
    db_name = config.MONGO_TEST_DB_NAME
    mongo_repo.ensure_thumbnail_job_details_indexes(db_name=db_name)
    job_id = str(uuid4())
    payload = {
        "reference_image_url": "https://example.com/ref.jpg",
        "base_image_urls": ["https://example.com/base.jpg"],
        "title": "Test title",
        "include_title": True,
        "creative_comments": "bold text",
        "model": "gptimage",
        "feedback": None,
        "prompt_used": None,
        "created_at": datetime.now(UTC),
    }
    mongo_repo.create_details(job_id, payload, db_name=db_name)
    found = mongo_repo.get_details(job_id, db_name=db_name)
    assert found is not None, "find after insert"
    assert found.get("job_id") == job_id
    print("insert + find OK for job_id", job_id)

    try:
        mongo_repo.create_details(job_id, payload, db_name=db_name)
    except DuplicateKeyError:
        print("duplicate job_id correctly rejected (unique index)")
    else:
        raise SystemExit("expected DuplicateKeyError on second insert with same job_id")

    mongo_repo.update_prompt_used(job_id, "prompt trace", db_name=db_name)
    after = mongo_repo.get_details(job_id, db_name=db_name)
    assert after and after.get("prompt_used") == "prompt trace"
    print("update_prompt_used OK")


if __name__ == "__main__":
    main()
