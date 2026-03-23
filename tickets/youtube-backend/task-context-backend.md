# Task Context — YouTube Script Automation Backend
## tools.scalebrandslab.com

---

## What This Task Is

Build the backend for the YouTube Script Automation tool — the first live tool on `tools.scalebrandslab.com`. This is a Python/FastAPI backend with MongoDB for persistence, Celery for background task processing, and Redis as the Celery broker (Redis is already running in the project's Docker setup).

The frontend for this tool is already specced out (see `workflow-plan.md`). This backend must serve that frontend. No new product decisions are being made here — all design decisions have been finalised.

---

## What This Tool Does (Product Summary)

The tool helps the Scale Brands Lab team find YouTube channels matching a set of search terms, filter them by quality criteria, and extract contact emails from channel descriptions. The user defines a **batch** — a named collection of search terms with filter parameters — and the system processes each term against the YouTube Data API, storing qualifying channels as leads.

Because the YouTube Data API has a **10,000 credit daily quota**, processing is spread across multiple days. The backend must track credit usage, pause when the limit is hit, and resume the next day from where it stopped.

---

## Source Script

The core YouTube processing logic already exists as a standalone Python script. The backend productises this script — it does not rewrite the logic, it wraps it into a resumable, persistent, multi-user job system.

**What the script does (in order):**
1. Takes a keyword + filter parameters as input
2. Searches YouTube for videos matching the keyword using 3 sort orders (`date`, `viewCount`, `relevance`), up to 60 pages total, collecting unique channel IDs — stops early on low yield or when 2,000 channels are collected
3. Fetches full channel details in batches of 50 (statistics, snippet, content details)
4. Evaluates each channel against filters: subscriber range, country exclusion, minimum video count, uploads in last 30 days, average views on recent videos
5. Extracts emails from channel descriptions via regex; flags `CAPTCHA` if contact language is present but no email found
6. Scores each qualifying channel: `(recent_uploads × 3) + (log10(subscribers) × 2) + (avg_views / 10,000)`
7. Returns qualifying channels as structured lead records

In the productised version, each search term in a batch goes through this full pipeline. The "keyword" in the script maps to a single "search term" from the batch.

---

## Architecture Decisions (All Final — Do Not Revisit)

### Stack
- **FastAPI** — REST API
- **MongoDB** — persistence (batches, terms, leads, daily usage, logs)
- **Celery** — background task processing
- **Redis** — Celery broker (already in Docker)
- **Celery Flower** — task monitoring dashboard (add as Docker service)

### Task Design
- **One orchestrator task per batch trigger** — lightweight, manages the processing loop
- **One process_term task per search term** — does the actual YouTube API work, bounded runtime (~2–5 min max per term)
- Tasks are chained sequentially — the orchestrator dispatches one term task, waits for it, then decides whether to continue or pause
- No parallel term processing — terms run one at a time to respect API rate limits

### Distributed Lock
- Redis lock key: `batch_lock:{batch_id}`, TTL 10 minutes
- Acquired by the orchestrator on start, released on completion/pause/error
- Prevents double-trigger from double-click, Celery retry, etc.
- Also enforces the one-batch-per-day rule at the worker level (in addition to API-level enforcement)

### Credit Tracking
- **MongoDB `daily_usage`** — authoritative, persists across restarts, what the frontend reads
- **Redis counter** — fast in-process tracking during a run, initialised from MongoDB at orchestrator start, incremented per API call
- Credit costs: search API = 100 credits/call, channels/playlistItems/videos APIs = 1 credit/call
- Updated in MongoDB after each term completes

### Daily Limit Behaviour
- Daily credit limit: **10,000 credits**
- When the limit is hit mid-term: roll back that term to `pending`, commit all leads from already-completed terms, mark batch as `paused`
- Partial results from a mid-run term are discarded (not worth the complexity of mid-term resumption)

### Filter Scope
- Filters are set at batch creation and stored on the batch document
- All search terms in a batch share the same filters — no per-term filter overrides
- Filters: `minSubs`, `maxSubs`, `minUploadsLast30d`, `minAvgViews` (optional, default 0), `excludeCountries` (default `["IN"]`), `region` (default `"US"`)

### Failure Handling
- If a term fails (YouTube API error, network error, unhandled exception): mark term as `failed`, log the error to `job_logs`, move on to the next term
- No automatic retries — failures are visible in Celery Flower for manual inspection
- A `failed` term does not block or stop the batch

### Batch State Machine
```
Batch:  queued → running → paused → running → ... → completed
                         → failed (unrecoverable, e.g. all terms failed)

Term:   pending → running → done
                          → failed
                          → pending (rolled back on credit limit mid-run)
```

### Frontend Polling
- Frontend polls `GET /credits/today` every 30s while a batch is running
- Frontend polls `GET /batches/:id` every 15s for progress
- No websockets — polling is sufficient

---

## Data Model (Collections)

### `batches`
```
_id, name, keyword, status,
filters: { minSubs, maxSubs, minUploadsLast30d, minAvgViews, excludeCountries, region },
totalTerms, processedTerms,
createdAt, lastTriggeredAt, completedAt
```

### `search_terms`
```
_id, batchId, term, status, position,
creditsUsed, channelsDiscovered, channelsQualified, emailsFound,
startedAt, completedAt, errorMessage
```

### `leads`
```
_id, batchId, searchTermId,
channelName, channelUrl, channelId,
subscribers, uploadsLast30d, avgViews, lastUpload,
score, country,
email, emailStatus,   # "found" | "captcha" | "none"
discoveredAt
```

### `daily_usage`
```
_id, date,            # "YYYY-MM-DD"
creditsUsed, creditLimit,
activeBatchId,
runsCompleted
```

### `job_logs`
```
_id, batchId, searchTermId,
event, message, timestamp
```

---

## API Endpoints

```
# Batches
GET    /batches                  list all batches with progress
POST   /batches                  create batch (validates term format)
GET    /batches/:id              batch detail + term list
POST   /batches/:id/trigger      start today's run (enforces daily lock)
DELETE /batches/:id              cancel / delete batch

# Leads
GET    /batches/:id/leads        paginated leads for a completed/running batch
GET    /batches/:id/export       CSV export (not in scope now — stub endpoint only)

# System
GET    /credits/today            { used, remaining, limit, activeBatchId, resetAt }
```

### POST /batches — Validation Rules
- `name`: required, non-empty string
- `keyword`: required, non-empty string (label only, not used in search)
- `terms`: required, array of strings, minimum 1 term
- `terms` format: each term must match — when the raw input string is parsed, every term must be wrapped in double quotes and separated by commas. Reject if any term is empty string after unquoting.
- `filters.minSubs`: required, integer ≥ 0
- `filters.maxSubs`: required, integer > minSubs
- `filters.minUploadsLast30d`: required, integer ≥ 1
- `filters.minAvgViews`: optional, integer ≥ 0, default 0

### POST /batches/:id/trigger — Rules
- Check `daily_usage` for today's date — if `activeBatchId` is set, return 400 with message identifying the already-running batch
- Check batch status — must be `queued` or `paused` to trigger; return 400 if `running` or `completed`
- Dispatches Celery orchestrator task asynchronously
- Returns 202 Accepted immediately

---

## File Structure (Proposed)

```
backend/
  app/
    api/
      routes/
        batches.py
        credits.py
    worker/
      orchestrator.py      # orchestrator Celery task
      process_term.py      # per-term Celery task
      youtube/
        search.py          # collect_channel_ids logic
        channels.py        # get_channel_details_batch logic
        evaluate.py        # evaluate_channel logic
        credits.py         # credit counting wrapper
    models/
      batch.py
      search_term.py
      lead.py
      daily_usage.py
    db.py                  # MongoDB connection
    celery_app.py          # Celery app init
    main.py                # FastAPI app init
  docker-compose.yml       # add worker + flower services
  .env
```

The YouTube processing logic from the source script maps directly into `worker/youtube/` — refactored into functions, not rewritten from scratch.

---

## Docker Services to Add

```yaml
worker:
  build: .
  command: celery -A app.celery_app worker --loglevel=info
  depends_on: [redis, mongo]
  env_file: .env

flower:
  build: .
  command: celery -A app.celery_app flower --port=5555
  ports:
    - "5555:5555"
  depends_on: [redis]
```

Redis and MongoDB services are assumed to already exist in the compose file.

---

## What Is Out of Scope for This Task

- CSV export (stub the endpoint, do not implement)
- Authentication / user accounts
- Cron-based auto-trigger (manual trigger only for now)
- Apify or Phase 4 email finder integration
- Per-term filter overrides
- Parallel term processing
- Websocket progress streaming

---

## Key Numbers to Keep in Mind

| Parameter | Value |
|---|---|
| Daily credit limit | 10,000 |
| Search API cost | 100 credits / call |
| Channels/playlist/video API cost | 1 credit / call |
| Max search pages (per term, all orders) | 60 pages |
| Worst-case credits per term | ~6,000+ |
| Realistic credits per term | ~1,500–3,000 |
| Estimated terms per day | 3–6 (not ~100 as shown in frontend mock) |
| Batch size of channel API calls | 50 IDs per request |
| Recent videos fetched per channel | 15 |
| Video stats fetched per channel | 20 |
| Redis lock TTL | 10 minutes |
| Stuck-term cleanup threshold | 30 minutes in `running` state |

> ⚠️ The frontend currently displays "~100 credits per search term" and "~100 terms per day" in its mock data. These numbers are wrong and must be corrected when the real credit tracking data is available. Do not build the backend around these frontend mock values.

---

## Reference Files

- `problem-context.md` — why this platform exists
- `workflow-plan.md` — frontend epic/story breakdown
- Source script — the original `youtube_lead_finder.py` being productised