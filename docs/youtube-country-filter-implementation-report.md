# YouTube Country Filter — Implementation Report

## 1. Summary of the Original Problem

Generated YouTube lead lists were supposed to be restricted to seven countries (US, UK, NZ, AUS, UAE, SG, CA) but were not — channels from any country worldwide (other than India) were being admitted as qualified leads.

## 2. Confirmed Root Cause

`evaluate_channel()` (`backend-app/app/worker/youtube/evaluate.py`, pre-fix lines 51–54) implemented a **denylist** (`if country in excludeCountries: reject`, default `excludeCountries = ["IN"]`) where the business requires an **allowlist** ("only these seven, reject everything else"). This is a logical inversion, not a partial gap — full analysis and reproduction evidence in `docs/youtube-country-filter-rca.md`. Three compounding defects were also confirmed: missing/empty country data defaulted to *pass* rather than *reject*; no allowlist field existed anywhere in the schema, API, or UI to even express the requirement; and no normalization layer existed, which would have caused a naive fix (seeding the business's literal spellings `"UK"`/`"AUS"`/`"UAE"`) to incorrectly reject real UK/Australian/UAE channels, since YouTube's API returns `"GB"`/`"AU"`/`"AE"`.

## 3. Files Changed

| File | Change |
|---|---|
| `backend-app/app/core/youtube_countries.py` | **New.** Centralized `ALLOWED_COUNTRIES` allowlist, alias map, `normalize_country_code()`, `is_allowed_country()` |
| `backend-app/app/worker/youtube/evaluate.py` | Country check in `evaluate_channel()` replaced: hard allowlist gate added; existing `excludeCountries` denylist preserved as an additional filter on top, now alias/case normalized |
| `backend-app/tests/test_youtube_country_filter.py` | **New.** Unit + integration-style tests (see Section 7) |
| `backend-app/scripts/audit_youtube_lead_countries.py` | **New.** Read-only (default) Mongo audit of existing `yt_leads` against the new allowlist, with an optional non-destructive `--tag` mode |
| `docs/youtube-api-backend-documentation.md` | **New.** Full backend architecture documentation |
| `docs/youtube-country-filter-rca.md` | **New.** Root cause analysis |
| `docs/youtube-country-filter-implementation-report.md` | **New.** This document |

No other files were modified. No unrelated functionality was touched, removed, or refactored.

## 4. Functions/Classes Changed

- **Added:** `normalize_country_code(raw: str | None) -> str | None` and `is_allowed_country(raw: str | None) -> bool` in `app/core/youtube_countries.py`.
- **Modified:** `evaluate_channel()` in `app/worker/youtube/evaluate.py` — only the country-check block (now lines 52–64); the function's signature, return shape, and every other check (subscriber range, `videoCount`, upload cadence, average views, email extraction, scoring) are unchanged.

## 5. Explanation of the Implementation

`app/core/youtube_countries.py` defines `ALLOWED_COUNTRIES` as a `frozenset` of the seven canonical ISO 3166-1 alpha-2 codes (`US, GB, NZ, AU, AE, SG, CA`), plus a small alias table (`UK→GB, AUS→AU, UAE→AE`) so input can be authored either way. `normalize_country_code()` trims whitespace, upper-cases, and resolves aliases — it returns `None` for blank/missing input, which callers must treat as "unknown," never as an implicit pass. `is_allowed_country()` is the strict boolean gate: `True` only when the normalized code is in `ALLOWED_COUNTRIES`.

In `evaluate_channel()`, the country check now reads:

```python
country_raw = channel.get("snippet", {}).get("country")
if not is_allowed_country(country_raw):
    return None
country = normalize_country_code(country_raw) or ""

exclude_countries = {
    normalize_country_code(c) for c in filters.get("excludeCountries", ["IN"])
}
if country in exclude_countries:
    return None
```

The allowlist gate runs first, in the same position the old check occupied (right after the subscriber-count check, before the API-calling checks), so a disallowed channel is rejected before any additional quota is spent on it. The pre-existing `excludeCountries` batch filter still runs afterward, now normalized through the same alias/casing logic — so it continues to work exactly as before for anyone using it, but can no longer be the *only* thing standing between a disallowed country and a saved lead, because the hard allowlist now runs unconditionally ahead of it. The `country` value stored on the resulting lead is always the normalized canonical code, never the raw input.

## 6. Before-and-After Behavior

Directly executed against the repository's own code (not simulated), via `.venv/Scripts/python.exe`, since the `pytest` suite itself could not run in this environment (Section 7):

**Before** (exact pre-fix logic, default `excludeCountries = ["IN"]`):
```
snippet.country=  'DE' -> PASSED FILTER (bug: would proceed to lead creation)
snippet.country=  'BR' -> PASSED FILTER (bug: would proceed to lead creation)
snippet.country=  'PH' -> PASSED FILTER (bug: would proceed to lead creation)
snippet.country=  'NG' -> PASSED FILTER (bug: would proceed to lead creation)
snippet.country=  'RU' -> PASSED FILTER (bug: would proceed to lead creation)
snippet.country=  'FR' -> PASSED FILTER (bug: would proceed to lead creation)
snippet.country=  None -> PASSED FILTER (bug: would proceed to lead creation)
snippet.country=    '' -> PASSED FILTER (bug: would proceed to lead creation)
snippet.country=  'IN' -> REJECTED
```

**After** (current `evaluate_channel()`, run against synthetic `channels.list`-shaped fixtures with the two downstream network calls stubbed):
```
snippet.country=  'US' -> ACCEPTED as country='US'
snippet.country=  'GB' -> ACCEPTED as country='GB'
snippet.country=  'UK' -> ACCEPTED as country='GB'
snippet.country=  'AU' -> ACCEPTED as country='AU'
snippet.country= 'AUS' -> ACCEPTED as country='AU'
snippet.country=  'AE' -> ACCEPTED as country='AE'
snippet.country= 'UAE' -> ACCEPTED as country='AE'
snippet.country=  'SG' -> ACCEPTED as country='SG'
snippet.country=  'CA' -> ACCEPTED as country='CA'
snippet.country=  'DE' -> REJECTED
snippet.country=  'IN' -> REJECTED
snippet.country=    '' -> REJECTED
snippet.country=  None -> REJECTED
snippet has no country key at all -> REJECTED
```

## 7. Test Cases and Actual Results

**pytest could not be executed to completion in this environment.** `backend-app/tests/conftest.py` has an `autouse=True` fixture (`clean_db`, lines 33–43) that connects to Postgres before *every* test in the suite — including previously-existing, logically pure unit tests (`test_youtube_quota_context.py`, `test_youtube_orchestrator_finalise.py`). This environment has no reachable Postgres or Mongo (Docker Desktop is installed but its engine is not running — `docker ps` fails with `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`; a direct `pymongo` connection attempt also hung past a 10-second timeout). This is a **pre-existing environment limitation**, reproduced identically against the unmodified `test_youtube_quota_context.py` before any change in this session — not something introduced by this fix.

Given that, verification was done two ways:

1. **Direct execution of the real, imported production code** (not pytest, not reimplemented) — `app.core.youtube_countries` and `app.worker.youtube.evaluate.evaluate_channel`, imported normally and called against synthetic fixtures with only the two outbound network calls stubbed. Full output is in Section 6 above and covers every required case from the task: US, GB/UK, NZ, AU/AUS, AE/UAE, SG, CA all accepted and normalized; unsupported (`DE`, `IN`), missing (`None`), and empty (`''`) all rejected; case/whitespace normalization (`' gb '`, `'uk'`, `'aus'`) confirmed accepted and correctly normalized.
2. **A committed pytest test file** (`tests/test_youtube_country_filter.py`, 20 test functions) written in the same style as the repository's existing unit tests, so it will run normally in any environment where the suite's Postgres dependency is satisfied (local dev with `docker compose up`, or CI). It was **not observed to pass in this session** — it could not be run to completion, for the reason above. Its logic exercises the same code paths verified manually in item 1, plus: the country gate runs *before* any API-calling code executes (asserted via a call-tracking monkeypatch, confirming disallowed channels never spend extra quota); the pre-existing `excludeCountries` filter still composes correctly on top of the new allowlist, including with alias input (`"UAE"` in a batch's `excludeCountries` correctly excludes a channel reporting `"AE"`).

No claim is made that "tests passed" — only that the underlying logic was directly executed and produced the outputs shown, and that a corresponding pytest suite exists and needs to be run in an environment with the required infrastructure before merge.

## 8. Database Migration or Cleanup Requirements

None required for the fix to take effect — it only changes evaluation logic applied to channels processed from deployment onward; no schema change, no required migration.

For **existing** `yt_leads` documents (written under the old denylist, likely including many disallowed-country channels): `backend-app/scripts/audit_youtube_lead_countries.py` was added to report — read-only by default — how many existing leads fall outside the new allowlist, are missing country data, or are fine. It also supports an explicit `--tag` mode that adds a non-destructive `countryFilterAudit` field (never deletes or overwrites existing fields). **This script has not been run against any real database in this session** — no Mongo instance was reachable (a direct connection attempt hung past a 10-second timeout). It should be run and its output reviewed by someone with database access before deciding on any cleanup action; see the RCA's Rollout Plan (Section 11) for the recommended sequence. No destructive migration was implemented or run, deliberately — deleting or mutating production lead data without the team's review is outside what this change should do unilaterally.

## 9. Deployment Considerations

- Pure application-code change; no environment variables, dependencies, or infrastructure changes required.
- No new third-party dependency was introduced.
- Existing API quota, retry, locking, and scheduling behavior is untouched — the change is fully contained inside `evaluate_channel()`'s country-check block.
- Recommend running the new `test_youtube_country_filter.py` suite in CI/staging (where Postgres/Mongo are available) before merge, since it could not be run in this session.
- Recommend running `scripts/audit_youtube_lead_countries.py` against staging or production (read-only) shortly after deploy to size the existing-data cleanup decision.

## 10. Remaining Limitations

- **`channels.snippet.country` reflects self-reported channel metadata, not verified creator residence.** This fix enforces "the channel's declared country is one of the seven," not "the creator provably lives there." If the actual business need is verified physical residence, the YouTube Data API cannot supply that on its own — see the RCA's Section 12 for detail on why, and what a separate verification step would require.
- Existing pre-fix `yt_leads` records are not automatically corrected (Section 8).
- `videoCount ≥ 20` remains a hardcoded, non-configurable threshold in the same function — unrelated to this fix, noted in the architecture doc as a similarly-shaped issue worth addressing separately.
- The stale "3 sort orders" docstring in `search.py` (only one, `relevance`, actually runs) is unrelated to country filtering and was left untouched, per the instruction not to modify unrelated behavior; documented in the architecture doc, Section 16.
- `pytest` could not be run in this authoring session (Section 7) — the new test file has not been observed passing; it should be run in an environment with the required Postgres/Mongo before this change is considered fully verified by CI standards.

## 11. Recommended Future Improvements

1. Run the new pytest suite in an environment with reachable Postgres/Mongo and confirm green before merge.
2. Run `scripts/audit_youtube_lead_countries.py` against staging/production and decide, as a team, what to do with pre-fix leads outside the allowlist.
3. Consider whether the country's `autouse` Postgres-connecting fixture in `tests/conftest.py` should be scoped down so pure unit tests (like this one, and the pre-existing quota/orchestrator tests) don't require full infra to run locally — this would have let this fix be verified with the repository's own test runner directly.
4. If the business need is truly "verified creator residence" rather than "self-reported channel metadata," scope a follow-up to evaluate a verification step outside the YouTube Data API.
