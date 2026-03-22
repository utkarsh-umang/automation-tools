# Task Context — YouTube Script Automation (tools.scalebrandslab.com)

## Current Task

Build the frontend for the **YouTube Script Automation** tool — the first and currently only live tool on `tools.scalebrandslab.com`. This is a React application. No backend is being built as part of this task. The frontend should be built assuming a REST API will back it later; use mock/static data where needed now.

## What This Tool Does

The YouTube Script Automation tool helps the Scale Brands Lab team find YouTube channels relevant to their clients and extract contact emails from those channels. The user defines a set of search terms, and the tool processes each term against the YouTube Data API to find matching channels and pull contact information.

Because the YouTube Data API has a **10,000 credit daily quota**, the tool cannot process unlimited search terms in one go. Processing is spread across multiple days. The user comes back each day to continue where they left off.

## Key Concepts

### Batch
A batch is the core unit of work. Each batch has:
- A **name** (user-defined, for reference)
- A **keyword** (a label/category for the batch, not used in the search itself)
- A **list of search terms** (each term is what gets sent to the YouTube API)
- A **completion percentage** that updates as terms are processed
- A **status**: `queued`, `running`, `paused`, or `completed`

### Search Terms Format
Search terms must be entered in a specific format: each term wrapped in double quotes, separated by commas.

Example: `"podcast host", "content creator", "youtube creator coaching", "video marketing agency"`

The frontend must validate this format before a batch can be created. Terms that don't match this format must be flagged inline before submission.

### Daily Credit Limit
- Total daily quota: **10,000 YouTube API credits**
- Approximate cost per search term: **~100 credits**
- This means approximately **100 search terms** can be processed per day
- A batch with more than ~100 terms will automatically pause when the daily limit is hit and resume the next day
- A user can only **trigger one batch per day** — once a batch has run today, no other batch can be triggered until tomorrow

### Batch Lifecycle
1. User creates a batch with a name, keyword, and list of search terms
2. Batch enters `queued` state
3. User (or system) triggers the batch — it begins processing terms one by one
4. If the daily credit limit is hit before all terms are processed, the batch pauses (`paused` state)
5. The next day, the user returns and triggers the batch again to continue
6. When all terms are processed, the batch is `completed`
7. Completed batches will eventually support CSV export (not in scope for this task)

### Multiple Batches
Users can have multiple batches at once. However:
- Only **one batch can be triggered per day**
- Other batches remain `queued` or `paused` while today's triggered batch is running

## What Is In Scope (This Task)

- Full React frontend for the YouTube Script tool
- App shell: sidebar navigation, tool routing
- Dashboard: tool cards overview
- YouTube Script tool view:
  - Batches list with progress bars, status badges, and daily credit meter
  - Create batch form with search term validation and live term preview
  - Batch detail view (per-term progress table, stats)
  - Completed batch view (export placeholder, disabled)
  - Daily lock state (prevent second trigger on same day)
- Static/mock data throughout — no real API calls required now

## What Is Out of Scope (This Task)

- Backend / API integration
- Email extraction logic
- Apify or Phase 4 connector integration
- Export functionality (CSV)
- Authentication / login
- Other tools (Library LP Creator, Podscan List Builder, Lead Magnet PDF, Thumbnail Project) — these are placeholders only

## Tech Stack

- React (existing application)
- Existing styling conventions of the project should be followed
- No new UI libraries should be introduced unless absolutely necessary

## Reference

See `workflow-plan.md` for the full JIRA-style epic and story breakdown of this task.