# Workflow Plan — YouTube Script Automation Frontend
## tools.scalebrandslab.com · JIRA-Style Epic & Story Breakdown

---

## EPIC 1 — App Shell & Navigation

**Summary:** Build the top-level application shell — the sidebar, routing structure, and screen layout — that all tools will live inside. This is the foundation every other epic depends on.

**Acceptance Criteria:**
- A persistent left sidebar renders on all screens
- Sidebar contains the Scale Brands Lab branding and tool links
- Each tool link has a label, icon, and status badge (Live / Soon)
- Clicking a tool navigates to its screen
- Active tool is visually highlighted in the sidebar
- Layout is responsive enough to not break at standard desktop widths

---

### Story 1.1 — Sidebar component

**As a** team member,
**I want** a persistent left sidebar with tool navigation,
**so that** I can access any tool from anywhere in the app without losing context.

**Tasks:**
- Create a `Sidebar` component with Scale Brands Lab wordmark and "Tools" sub-label at the top
- Render a nav item for each tool: YouTube Script, Library LP Creator, Podscan List, Lead Magnet PDF, Thumbnail Project
- Each nav item has: a small SVG icon, a label, and a status badge (`Live` in green, `Soon` in gray)
- Active nav item gets a left-border accent and bold label
- Sidebar width: fixed, ~210px

**Mock data:** Hardcode the tool list as a static array with `{ id, label, icon, status, path }` shape.

---

### Story 1.2 — App layout and routing

**As a** team member,
**I want** clicking a sidebar item to navigate to the correct tool screen,
**so that** each tool is reachable via its own route.

**Tasks:**
- Set up React Router with the following routes:
  - `/` → redirects to `/dashboard`
  - `/dashboard` → Dashboard screen
  - `/youtube-script` → YouTube Script tool
  - `/library-lp` → Library LP Creator (placeholder)
  - `/podscan` → Podscan List Builder (placeholder)
  - `/lead-magnet-pdf` → Lead Magnet PDF (placeholder)
  - `/thumbnail` → Thumbnail Project (placeholder)
- Wrap routes in the `AppShell` layout (Sidebar + main content area)
- Main content area takes up remaining width after the sidebar

---

### Story 1.3 — Placeholder screens for non-live tools

**As a** team member,
**I want** the non-live tools to show a "coming soon" placeholder,
**so that** the navigation is complete and the app doesn't have broken routes.

**Tasks:**
- Create a reusable `ComingSoonScreen` component that accepts `title` and `description` props
- Render it for: Library LP Creator, Podscan List, Lead Magnet PDF, Thumbnail Project
- Each placeholder shows the tool name, a short description, and a "Planned" badge

---

## EPIC 2 — Dashboard

**Summary:** Build the dashboard — the home screen of the platform — which shows all available tools as cards and provides quick entry into each tool.

**Acceptance Criteria:**
- Dashboard renders a grid of tool cards
- YouTube Script card is featured (full-width or visually dominant) since it is the only live tool
- Each card shows: tool name, description, tags, status badge
- Clicking any card navigates to that tool's screen

---

### Story 2.1 — Tool card component

**As a** team member,
**I want** to see all tools as cards on the dashboard,
**so that** I can understand what's available and navigate quickly.

**Tasks:**
- Create a `ToolCard` component accepting: `title`, `description`, `tags[]`, `status`, `onClick`
- Status drives the badge: `live` → green "Live" badge, `planned` → gray "Planned" badge
- Tags render as small pill labels below the description
- Card has a hover border state

---

### Story 2.2 — Dashboard screen layout

**As a** team member,
**I want** the YouTube Script tool to be visually prominent on the dashboard,
**so that** it's clear which tool is active and ready to use.

**Tasks:**
- Dashboard renders a 2-column grid of `ToolCard` components
- YouTube Script card spans full width (2 columns) with a mini workflow preview on the right side showing the batch lifecycle steps: Create batch → Daily run → Track progress → Export
- Other four tools render as standard single-column cards below
- Page has a header: "Tools Workspace" with a sub-label

---

## EPIC 3 — YouTube Script Tool — Batch Management

**Summary:** Build the main YouTube Script tool screen, which is split into two tabs: "My Batches" (list of existing batches) and "Create Batch" (form to create a new one). This epic covers the batches list and all the states a batch can be in.

**Acceptance Criteria:**
- Tool screen has two tabs: My Batches and Create Batch
- My Batches tab shows all batches with correct status, progress, and metadata
- Daily credit meter renders at the top of the batches list
- Daily lock notice renders if a batch has already been triggered today
- Clicking a batch opens its detail view

---

### Story 3.1 — Tool screen header and tab navigation

**As a** team member,
**I want** the YouTube Script tool to have a tab bar for switching between my batches and creating a new one,
**so that** batch management and batch creation are clearly separated.

**Tasks:**
- Render a tool screen header with title, description, and a "+ New Batch" button (shortcut to Create Batch tab)
- Render two tabs: "My Batches" and "Create Batch"
- Active tab has a bottom border accent
- Tab switching shows/hides the corresponding view without re-mounting
- "+ New Batch" button switches to the Create Batch tab

---

### Story 3.2 — Daily credit meter

**As a** team member,
**I want** to see how many YouTube API credits I've used today and how many remain,
**so that** I know how many more search terms can be processed today.

**Tasks:**
- Render a credit meter bar at the top of the My Batches view
- Shows: credits used today, credits remaining, a progress bar, and "Resets daily · 10,000 credit limit" label
- Progress bar changes color when usage is above 80% (e.g. amber/orange)
- Use mock data: hardcode a `dailyCreditsUsed` value to demonstrate different states

---

### Story 3.3 — Daily lock notice

**As a** team member,
**I want** to see a notice when a batch has already been triggered today,
**so that** I know I cannot trigger another batch until tomorrow.

**Tasks:**
- If `todaysBatchId` is set (a batch was already triggered today), render a warning banner above the batch list
- Banner text: identifies which batch is running today and states that another batch can be triggered tomorrow
- Banner uses a warning color (amber/yellow treatment)
- If no batch has been triggered today, the banner does not render

---

### Story 3.4 — Batch list card component

**As a** team member,
**I want** to see all my batches as cards with their status and progress,
**so that** I can quickly see which batches are done, running, or waiting.

**Tasks:**
- Create a `BatchCard` component accepting: `name`, `keyword`, `totalTerms`, `processedTerms`, `status`, `createdAt`, `onClick`
- Status options and their visual treatment:
  - `running` → blue "Running today" badge
  - `paused` → amber "Paused — continue tomorrow" badge
  - `completed` → green "Completed" badge
  - `queued` → gray "Queued" badge
- Progress bar shows `processedTerms / totalTerms` as a percentage
- Progress info line shows: "X of Y terms processed" on the left, percentage on the right
- Completed batches show "Export available" text on the right in green instead of percentage
- Card is clickable and opens the batch detail view

**Mock data:** Create a static array of 3 batches representing the four states (one running, one paused, one completed).

---

### Story 3.5 — Batches list view

**As a** team member,
**I want** to see all my batches in one scrollable list,
**so that** I can manage multiple active batches at the same time.

**Tasks:**
- Render the `BatchCard` list inside the My Batches tab
- Render the daily credit meter above the list
- Render the daily lock notice below the credit meter if applicable
- Section label "Active batches" above the list
- Empty state: if no batches exist, show a message prompting the user to create their first batch with a link to the Create Batch tab

---

## EPIC 4 — YouTube Script Tool — Create Batch

**Summary:** Build the Create Batch form, including the search terms input with live format validation and parsed term preview.

**Acceptance Criteria:**
- User can enter a batch name, keyword, and search terms
- Search terms are validated against the `"term", "term"` format in real time
- Parsed terms are shown as visual tokens below the input
- Validation errors are shown inline, not on submit
- A valid submission creates the batch (mock) and returns the user to the batches list

---

### Story 4.1 — Create batch form layout

**As a** team member,
**I want** a clean form to create a new batch,
**so that** I can define the name, keyword, and search terms before running it.

**Tasks:**
- Render a form with three sections:
  1. Batch name (text input, required)
  2. Keyword / category (text input, required — explain in helper text that this is a label, not a search filter)
  3. Search terms (textarea, required)
- Add an info banner explaining the 10,000 daily credit limit and that batches with more than ~100 terms will run across multiple days
- "Create Batch" primary button and "Cancel" secondary button in the footer

---

### Story 4.2 — Search terms format validation

**As a** team member,
**I want** the search terms field to validate my input as I type,
**so that** I know immediately if my format is wrong before I try to submit.

**Tasks:**
- Validation rule: every term must be wrapped in double quotes (`"`), and terms must be separated by commas. Any text outside of quoted terms (other than commas and whitespace) is invalid.
- Validate on every `onChange` event (live, not on blur or submit)
- If the format is invalid, show an inline error message below the textarea: _"Some terms are not formatted correctly — make sure every term is wrapped in double quotes and separated by commas."_
- If the format is valid, the error message disappears
- The "Create Batch" submit button should be disabled while there is an active validation error

**Validation logic (implement exactly):**
```
1. Strip all valid quoted terms: /"[^"]+"/g
2. Remove all commas from what remains
3. Trim whitespace from what remains
4. If anything is left over (length > 0), the format is invalid
```

---

### Story 4.3 — Live term preview

**As a** team member,
**I want** to see my search terms parsed and displayed as individual tokens as I type,
**so that** I can confirm the system has read my terms correctly before creating the batch.

**Tasks:**
- Below the textarea, render a preview area labelled "Preview — N terms"
- As the user types valid terms, each term renders as a styled token (pill/chip) showing the term text without quotes
- If the input is empty, show placeholder text: "Parsed terms will appear here..."
- If the format is invalid, show an error state in the preview area: "Fix formatting above to see preview"
- Term count in the label updates dynamically: "Preview — 4 terms"

---

### Story 4.4 — Batch creation submission

**As a** team member,
**I want** clicking "Create Batch" to create the batch and return me to the batches list,
**so that** I can see my new batch and trigger it when ready.

**Tasks:**
- On submit, validate all fields (name, keyword, search terms format)
- If any field is missing or invalid, show field-level errors and do not submit
- On valid submit: add the new batch to the mock data store with status `queued`, `processedTerms: 0`, and current timestamp as `createdAt`
- Navigate back to the My Batches tab
- The new batch should appear in the batches list with a "Queued" status badge

---

## EPIC 5 — YouTube Script Tool — Batch Detail Views

**Summary:** Build the three batch detail screens (in-progress, paused, and completed), each accessible by clicking a batch card from the list.

**Acceptance Criteria:**
- Each batch status has a tailored detail view
- All detail views show batch metadata, a summary stats block, and a back navigation
- In-progress and paused views show per-term progress table
- Completed view shows result summary and disabled export button

---

### Story 5.1 — Batch detail header and navigation

**As a** team member,
**I want** clicking a batch to open a detail view with a back button,
**so that** I can drill into any batch and return to the list easily.

**Tasks:**
- Create a `BatchDetailHeader` component showing: batch name, keyword, total terms, created date, status badge
- Render a "← Back to batches" button that returns to the My Batches tab
- This header is shared across all three detail view states

---

### Story 5.2 — In-progress batch detail

**As a** team member,
**I want** to see real-time progress on a running batch including a per-term breakdown,
**so that** I know exactly which terms have been processed, which is running, and which are pending.

**Tasks:**
- Render a summary stats block with: terms processed, terms currently running (0 or 1), terms remaining
- Render a large progress bar with percentage label
- Render a per-term table with columns: Search Term | Credits Used | Status
- Status options per row: `done` (green), `running` (blue), `pending` (gray)
- Credits used is blank (`—`) for pending and running terms
- Table rows are sorted: done first, then running, then pending

**Mock data:** Hardcode ~18 rows mixing done, one running, and remaining as pending.

---

### Story 5.3 — Paused batch detail

**As a** team member,
**I want** to see why a batch is paused and when I can continue it,
**so that** I know to come back tomorrow and continue.

**Tasks:**
- Render a warning banner: "This batch is paused — another batch is already running today. Come back tomorrow to continue processing the remaining X terms."
- Render the same summary stats block as Story 5.2 (processed, remaining, estimated days to complete)
- "Est. to complete" stat calculates as: `Math.ceil(remainingTerms / 100)` days
- Progress bar shows current completion percentage
- No per-term table needed for paused view (keep it light)

---

### Story 5.4 — Completed batch detail

**As a** team member,
**I want** to see a summary of a completed batch and know that export is coming,
**so that** I have closure on the batch and know what to expect next.

**Tasks:**
- Render a success banner: "All X search terms have been processed. Export is available below."
- Render a 3-stat summary: Terms Processed | Channels Found | Emails Extracted (mock numbers)
- Render an info banner: "Export functionality is coming soon — results will be downloadable as CSV."
- Render a disabled "Export CSV (coming soon)" primary button
- Render "← Back to batches" secondary button

---

## EPIC 6 — State Management & Mock Data Layer

**Summary:** Set up a lightweight mock data layer and shared state so that batch creation, navigation between views, and status changes all work consistently without a real backend.

**Acceptance Criteria:**
- All batch data flows from a single mock data source
- Creating a batch updates the shared state and reflects immediately in the batches list
- Navigation between tabs and detail views does not reset state
- Daily credit usage and daily lock state are derived from mock data

---

### Story 6.1 — Mock data store

**As a** developer,
**I want** a centralised mock data file,
**so that** all components read from the same source and the UI is consistent.

**Tasks:**
- Create `mockData.js` (or equivalent) with:
  - `batches[]`: 3 pre-seeded batches in different states (running, paused, completed)
  - `dailyCreditsUsed`: a number between 0–10000
  - `todaysBatchId`: the ID of the batch triggered today (or `null`)
  - `dailyCreditLimit`: 10000
  - `creditsPerTerm`: 100
- Export these as named constants

---

### Story 6.2 — Local state for batch creation

**As a** developer,
**I want** batch creation to update the in-memory batch list,
**so that** a newly created batch appears in the list without a page reload.

**Tasks:**
- Use React state (useState or useReducer) at the YouTube Script tool level to hold the batch list
- Initialise from `mockData.batches`
- On batch creation, append the new batch to state with `status: 'queued'`
- Pass the batch list and setter down to child components via props or context

---

### Story 6.3 — Derived daily state

**As a** developer,
**I want** the daily lock and credit meter to derive their values from the mock data,
**so that** changing `dailyCreditsUsed` or `todaysBatchId` in the mock file immediately reflects in the UI.

**Tasks:**
- `creditsRemaining = dailyCreditLimit - dailyCreditsUsed`
- `creditUsagePercent = (dailyCreditsUsed / dailyCreditLimit) * 100`
- `isDailyLocked = todaysBatchId !== null`
- `todaysBatchName` = look up batch name from `batches[]` by `todaysBatchId`
- Pass these derived values into the credit meter and lock notice components

---

## Summary — Epic Order

| # | Epic | Priority | Depends On |
|---|------|----------|------------|
| 1 | App Shell & Navigation | P0 | — |
| 2 | Dashboard | P1 | Epic 1 |
| 6 | State Management & Mock Data | P1 | — |
| 3 | Batch Management (list + tabs) | P1 | Epic 1, Epic 6 |
| 4 | Create Batch | P2 | Epic 3, Epic 6 |
| 5 | Batch Detail Views | P2 | Epic 3, Epic 6 |

Build in this order: **1 → 6 → 3 → 2 → 4 → 5**

---

## Design Notes for Cursor

- Follow the existing component and styling conventions of the project exactly — do not introduce new UI libraries
- All forms use controlled inputs (React state)
- Search term validation runs on `onChange`, not on blur or submit
- Validation logic must match the spec in Story 4.2 exactly — strip quoted terms, remove commas, check for leftover content
- Status badge colors: running = blue, paused = amber/yellow, completed = green, queued = gray
- Progress bars use percentage derived from `processedTerms / totalTerms * 100`
- The daily lock state and credit meter should be easy to demo by editing values in `mockData.js`
- No real API calls — all data is local/static for now