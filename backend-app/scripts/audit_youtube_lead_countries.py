#!/usr/bin/env python3
"""Audit existing ``yt_leads`` records against the new country allowlist.

Context: app/worker/youtube/evaluate.py previously used a denylist
(``excludeCountries``, default ``["IN"]``) instead of the allowlist in
app/core/youtube_countries.py. Every lead created before that fix may carry
a country outside the seven-country allowlist (US, GB, NZ, AU, AE, SG, CA),
or no country at all. See docs/youtube-country-filter-rca.md.

This script is READ-ONLY by default: it reports what exists, grouped by
whether it would pass the new allowlist. It never deletes anything.

Optional ``--tag`` mode adds a non-destructive, reversible audit field to
each lead (``countryFilterAudit: {status, auditedAt}``) so the product team
can filter stale records in the UI/exports without losing history. It never
deletes or mutates any existing field.

Usage (from backend-app/)::

    poetry run python scripts/audit_youtube_lead_countries.py                # report only
    poetry run python scripts/audit_youtube_lead_countries.py --batch-id ID  # scope to one batch
    poetry run python scripts/audit_youtube_lead_countries.py --tag          # report + tag stale docs

Requires Mongo reachable at the configured MONGO_LOCAL_URI / MONGO_PROD_URI.
This script was written and unit-verified logically, but has NOT been run
against a live database in the authoring session -- no Mongo instance was
reachable there (see docs/youtube-country-filter-implementation-report.md).
Review its query/update shape before running it against production data.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_ROOT = _BACKEND.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")
load_dotenv(_BACKEND / "local.env", override=True)

from app.core.youtube_countries import ALLOWED_COUNTRIES, normalize_country_code
from app.mongo.get_connection import get_database_connection

COLLECTION = "yt_leads"


def _classify(raw: object) -> str:
    if raw is None or raw == "":
        return "missing"
    code = normalize_country_code(str(raw))
    if code is None:
        return "missing"
    return "ok" if code in ALLOWED_COUNTRIES else "outside_allowlist"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default=None, help="Scope the audit to one batch")
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Additionally write a non-destructive countryFilterAudit field on each lead",
    )
    args = parser.parse_args()

    db = get_database_connection()
    coll = db[COLLECTION]

    query: dict = {"batchId": args.batch_id} if args.batch_id else {}
    docs = list(coll.find(query, {"_id": 1, "country": 1, "channelId": 1, "batchId": 1}))

    status_counts: Counter[str] = Counter()
    raw_value_counts: Counter[str] = Counter()
    for doc in docs:
        raw = doc.get("country")
        status = _classify(raw)
        status_counts[status] += 1
        raw_value_counts[str(raw)] += 1

    total = len(docs)
    print(f"yt_leads audited: {total}" + (f" (batchId={args.batch_id})" if args.batch_id else ""))
    for status in ("ok", "outside_allowlist", "missing"):
        n = status_counts.get(status, 0)
        pct = (n / total * 100) if total else 0
        print(f"  {status:<18} {n:>7}  ({pct:5.1f}%)")

    print("\nTop 20 raw country values by frequency:")
    for value, n in raw_value_counts.most_common(20):
        print(f"  {value!r:>8}  {n}")

    if not args.tag:
        print("\n(dry run -- pass --tag to add a non-destructive countryFilterAudit field)")
        return

    now = datetime.now(UTC)
    tagged = 0
    for doc in docs:
        status = _classify(doc.get("country"))
        if status == "ok":
            continue
        coll.update_one(
            {"_id": doc["_id"]},
            {"$set": {"countryFilterAudit": {"status": status, "auditedAt": now}}},
        )
        tagged += 1
    print(f"\nTagged {tagged} lead(s) with countryFilterAudit (non-destructive, additive only).")


if __name__ == "__main__":
    main()
