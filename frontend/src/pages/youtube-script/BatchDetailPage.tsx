import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import {
  getApiErrorMessage,
  type SearchTermItem,
  type TermStatus,
  useBatchDetailQuery,
  useBatchLeadsQuery,
  useCreditsTodayQuery,
  useExportBatchMutation,
  useFinalizeBatchMutation,
  useTriggerBatchMutation,
} from '@/hooks/api/useYoutubeApi'
import { ChevronDown, CircleQuestionMark } from 'lucide-react'

export function BatchDetailPage() {
  const { batchId } = useParams<{ batchId: string }>()
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [statsAccordionOpen, setStatsAccordionOpen] = useState(false)
  const pageSize = 10
  const detailQuery = useBatchDetailQuery(batchId, 10_000)
  const creditsQuery = useCreditsTodayQuery(10_000)
  const triggerMutation = useTriggerBatchMutation()
  const finalizeMutation = useFinalizeBatchMutation()
  const exportMutation = useExportBatchMutation()
  const shouldPollLeads = detailQuery.data?.status === 'running' || detailQuery.data?.status === 'paused'
  const leadsQuery = useBatchLeadsQuery(batchId, page, pageSize, shouldPollLeads ? 10_000 : 0)
  const batch = detailQuery.data

  function goBack() {
    navigate('/youtube-script')
  }

  if (detailQuery.isLoading) {
    return (
      <AppShell breadcrumb="YouTube Script">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <p className="text-sm" style={{ color: '#6b7280' }}>
            Loading batch...
          </p>
        </div>
      </AppShell>
    )
  }

  if (detailQuery.isError) {
    return (
      <AppShell breadcrumb="YouTube Script">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <p className="text-sm" style={{ color: '#be123c' }}>
            {getApiErrorMessage(detailQuery.error)}
          </p>
          <button
            type="button"
            onClick={goBack}
            className="mt-4 text-sm font-medium"
            style={{ color: '#2563eb' }}
          >
            ← Back to batches
          </button>
        </div>
      </AppShell>
    )
  }

  if (!batch) {
    return (
      <AppShell breadcrumb="YouTube Script">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <p className="text-sm" style={{ color: '#6b7280' }}>
            Batch not found.
          </p>
          <button
            type="button"
            onClick={goBack}
            className="mt-4 text-sm font-medium"
            style={{ color: '#2563eb' }}
          >
            ← Back to batches
          </button>
        </div>
      </AppShell>
    )
  }

  const remaining = Math.max(0, batch.totalTerms - batch.processedTerms)
  const pct = batch.totalTerms > 0 ? Math.round((batch.processedTerms / batch.totalTerms) * 100) : 0
  const terms = batch.terms ?? []
  const leadsData = leadsQuery.data
  const totalEmailsFound = terms.reduce((sum, term) => sum + (term.emailsFound ?? 0), 0)
  const canTrigger = batch.status === 'queued' || batch.status === 'paused'
  const blockedByOtherBatch =
    Boolean(creditsQuery.data?.activeBatchId) && creditsQuery.data?.activeBatchId !== batch._id

  const statusTone: Record<string, { bg: string; border: string; color: string; label: string }> = {
    running: { bg: 'rgba(37,99,235,0.08)', border: 'rgba(37,99,235,0.25)', color: '#1d4ed8', label: 'Running' },
    paused: { bg: '#fffbeb', border: '#fcd34d', color: '#b45309', label: 'Paused' },
    completed: { bg: '#f0fdf4', border: '#bbf7d0', color: '#15803d', label: 'Completed' },
    finalized: { bg: '#eff6ff', border: '#93c5fd', color: '#1d4ed8', label: 'Finalized' },
    queued: { bg: '#f9fafb', border: '#e5e7eb', color: '#6b7280', label: 'Queued' },
    failed: { bg: '#fff1f2', border: '#fecdd3', color: '#be123c', label: 'Failed' },
  }
  const tone = statusTone[batch.status] ?? statusTone.queued
  const runningTerms = terms.filter((r) => r.status === 'running').length
  const queuedView = batch.status === 'queued'

  return (
    <AppShell breadcrumb="YouTube Script">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between rounded-xl border px-3 py-2.5" style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}>
          <div className="min-w-0">
            <button
              type="button"
              onClick={goBack}
              className="mb-1 inline-flex items-center gap-1 text-xs font-medium"
              style={{ color: '#2563eb' }}
            >
              ← Back to batches
            </button>
            <div className="flex items-center gap-2">
              <h1 className="truncate text-base font-semibold" style={{ color: '#0a0f1e' }}>
                {batch.name}
              </h1>
              <span
                className="rounded px-2 py-0.5 text-[11px] font-semibold"
                style={{ backgroundColor: tone.bg, border: `1px solid ${tone.border}`, color: tone.color }}
              >
                {tone.label}
              </span>
            </div>
            <p className="text-xs" style={{ color: '#6b7280' }}>
              {batch.keyword} · {batch.totalTerms} terms
            </p>
          </div>
          <div className="flex flex-col items-end gap-1">
            {(exportMutation.isError || finalizeMutation.isError) && (
              <p className="text-xs font-medium" style={{ color: '#be123c' }}>
                {getApiErrorMessage(exportMutation.error ?? finalizeMutation.error)}
              </p>
            )}
            {finalizeMutation.isSuccess && (
              <p className="text-xs font-medium" style={{ color: '#15803d' }}>
                Finalized — {finalizeMutation.data.duplicatesRemoved} duplicates removed
              </p>
            )}
            <div className="flex items-center gap-2">
            {batch.status === 'completed' && (
              <button
                type="button"
                onClick={() => finalizeMutation.mutate(batch._id)}
                disabled={finalizeMutation.isPending}
                title="Deduplicate channels and finalize batch"
                className="rounded-lg px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                style={{
                  background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                  boxShadow: '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)',
                }}
              >
                {finalizeMutation.isPending ? 'Finalizing...' : 'Finalize Batch'}
              </button>
            )}
            {batch.status === 'finalized' && (
              <button
                type="button"
                onClick={() => exportMutation.mutate(batch._id)}
                disabled={exportMutation.isPending}
                title="Download all leads as CSV"
                className="rounded-lg px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                style={{
                  background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                  boxShadow: '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)',
                }}
              >
                {exportMutation.isPending ? 'Exporting...' : 'Export CSV'}
              </button>
            )}
            {canTrigger && !blockedByOtherBatch && (
              <button
                type="button"
                onClick={() => triggerMutation.mutate(batch._id)}
                disabled={triggerMutation.isPending}
                className="rounded-lg px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                style={{ background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' }}
              >
                {triggerMutation.isPending ? 'Triggering...' : 'Trigger'}
              </button>
            )}
            </div>
          </div>
        </div>

        <StatsAccordion
          open={statsAccordionOpen}
          onToggle={() => setStatsAccordionOpen((o) => !o)}
          processedTerms={batch.processedTerms}
          remaining={remaining}
          runningTerms={runningTerms}
          channelsTotal={leadsData?.total ?? 0}
          emailsTotal={totalEmailsFound}
          terms={terms}
        />

        <div className="rounded-xl border p-2.5" style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}>
          <div className="mb-1 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
              Batch Progress
            </p>
            <span className="text-xs tabular-nums font-semibold" style={{ color: '#2563eb' }}>
              {pct}%
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full" style={{ backgroundColor: '#f3f4f6' }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${pct}%`,
                background: 'linear-gradient(90deg, #2563eb, #1d4ed8)',
              }}
            />
          </div>
        </div>

        {queuedView ? (
          <div className="rounded-xl border px-4 py-4 text-sm" style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff', color: '#6b7280' }}>
            This batch is queued. Trigger it to start processing. Leads will appear here as terms are processed.
          </div>
        ) : (
          <LeadsTableSection
            leadsData={leadsData}
            terms={terms}
            isLoading={leadsQuery.isLoading}
            isError={leadsQuery.isError}
            error={leadsQuery.error}
            page={page}
            pageSize={pageSize}
            onPrev={() => setPage((p) => Math.max(1, p - 1))}
            onNext={() => setPage((p) => p + 1)}
          />
        )}
      </div>
    </AppShell>
  )
}

const statsAccordionPanelId = 'batch-stats-term-analytics'

interface StatsAccordionProps {
  open: boolean
  onToggle: () => void
  processedTerms: number
  remaining: number
  runningTerms: number
  channelsTotal: number
  emailsTotal: number
  terms: SearchTermItem[]
}

function StatsAccordion({
  open,
  onToggle,
  processedTerms,
  remaining,
  runningTerms,
  channelsTotal,
  emailsTotal,
  terms,
}: StatsAccordionProps) {
  return (
    <div className="rounded-xl border" style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}>
      <div className="flex items-stretch gap-2 p-3">
        <div className="grid min-w-0 flex-1 grid-cols-2 gap-2 sm:grid-cols-5">
          <Stat label="Processed" value={String(processedTerms)} compact />
          <Stat label="Remaining" value={String(remaining)} compact />
          <Stat label="Running" value={String(runningTerms)} compact />
          <Stat label="Channels" value={String(channelsTotal)} compact />
          <Stat label="Emails" value={String(emailsTotal)} compact />
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="flex shrink-0 items-center justify-center self-center rounded-lg border p-2 transition-colors hover:bg-gray-50"
          style={{ borderColor: '#e5e7eb' }}
          aria-expanded={open}
          aria-controls={statsAccordionPanelId}
          title={open ? 'Hide term analytics' : 'Show term analytics'}
        >
          <ChevronDown
            size={20}
            strokeWidth={2}
            className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
            style={{ color: '#6b7280' }}
            aria-hidden
          />
        </button>
      </div>
      <div
        id={statsAccordionPanelId}
        role="region"
        aria-label="Search term analytics"
        className={`grid transition-[grid-template-rows] duration-200 ease-out ${open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}
      >
        <div className="overflow-hidden">
          <div className="border-t px-3 pb-3 pt-2" style={{ borderColor: '#e5e7eb' }}>
            <TermAnalyticsTable terms={terms} />
          </div>
        </div>
      </div>
    </div>
  )
}

const TERM_ANALYTICS_PAGE_SIZE = 5

function TermAnalyticsTable({ terms }: { terms: SearchTermItem[] }) {
  const [page, setPage] = useState(1)

  const totalTerms = terms.length
  const totalPages = Math.max(1, Math.ceil(totalTerms / TERM_ANALYTICS_PAGE_SIZE))

  useEffect(() => {
    setPage((p) => Math.min(p, totalPages))
  }, [totalPages])

  if (terms.length === 0) {
    return (
      <p className="py-2 text-sm" style={{ color: '#6b7280' }}>
        No search terms in this batch.
      </p>
    )
  }

  const start = (page - 1) * TERM_ANALYTICS_PAGE_SIZE
  const pageRows = terms.slice(start, start + TERM_ANALYTICS_PAGE_SIZE)

  return (
    <div className="flex flex-col overflow-hidden rounded-lg border" style={{ borderColor: '#e5e7eb' }}>
      <p className="border-b px-3 py-2 text-[11px] font-semibold uppercase tracking-wide" style={{ borderColor: '#e5e7eb', color: '#6b7280' }}>
        By search term
      </p>
      <div
        className="grid grid-cols-12 gap-2 border-b px-3 py-2 text-[11px] font-semibold uppercase tracking-wide"
        style={{
          borderColor: 'rgba(37,99,235,0.2)',
          color: 'rgba(255,255,255,0.65)',
          background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 60%, #0a0f1e 100%)',
        }}
      >
        <div className="col-span-5 sm:col-span-6">Search term</div>
        <div className="col-span-4 sm:col-span-4">Status</div>
        <div className="col-span-3 sm:col-span-2 text-right">
          <span className="inline-flex items-center justify-end gap-1">
            Results
            <TermResultsTooltipIcon />
          </span>
        </div>
      </div>
      <div className="divide-y" style={{ borderColor: '#f3f4f6' }}>
        {pageRows.map((t) => {
          const tone = termStatusTone(t.status)
          const results = formatTermResults(t)
          return (
            <div key={t._id} className="grid grid-cols-12 gap-2 px-3 py-2 text-sm items-center">
              <div className="col-span-5 truncate sm:col-span-6" style={{ color: '#111827' }} title={t.term}>
                {t.term}
              </div>
              <div className="col-span-4 sm:col-span-4">
                <span
                  className="inline-block max-w-full truncate rounded px-2 py-0.5 text-[11px] font-semibold"
                  style={{
                    backgroundColor: tone.bg,
                    border: `1px solid ${tone.border}`,
                    color: tone.color,
                  }}
                  title={t.status === 'failed' && t.errorMessage ? t.errorMessage : undefined}
                >
                  {tone.label}
                </span>
              </div>
              <div className="col-span-3 text-right tabular-nums sm:col-span-2" style={{ color: '#6b7280' }}>
                {results}
              </div>
            </div>
          )
        })}
      </div>
      <div className="flex items-center justify-between border-t px-3 py-2" style={{ borderColor: '#e5e7eb' }}>
        <span className="text-xs" style={{ color: '#6b7280' }}>
          {totalTerms} search term{totalTerms === 1 ? '' : 's'}
        </span>
        {totalTerms > TERM_ANALYTICS_PAGE_SIZE && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded border px-2.5 py-1 text-xs disabled:opacity-50"
              style={{ borderColor: '#e5e7eb' }}
            >
              Prev
            </button>
            <span className="text-xs" style={{ color: '#6b7280' }}>
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="rounded border px-2.5 py-1 text-xs disabled:opacity-50"
              style={{ borderColor: '#e5e7eb' }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function termStatusTone(status: TermStatus): { label: string; bg: string; border: string; color: string } {
  switch (status) {
    case 'done':
      return { label: 'Completed', bg: '#f0fdf4', border: '#bbf7d0', color: '#15803d' }
    case 'running':
      return { label: 'Running', bg: 'rgba(37,99,235,0.08)', border: 'rgba(37,99,235,0.25)', color: '#1d4ed8' }
    case 'pending':
      return { label: 'Yet to process', bg: '#f9fafb', border: '#e5e7eb', color: '#6b7280' }
    case 'failed':
      return { label: 'Failed', bg: '#fff1f2', border: '#fecdd3', color: '#be123c' }
    default:
      return { label: status, bg: '#f9fafb', border: '#e5e7eb', color: '#6b7280' }
  }
}

/** Qualified channels stored for this term (after filters). Pending/running: not available yet. */
function formatTermResults(term: SearchTermItem): string {
  if (term.status === 'pending' || term.status === 'running') {
    return '—'
  }
  return String(term.channelsQualified ?? 0)
}

function TermResultsTooltipIcon() {
  return (
    <span className="group relative inline-flex">
      <CircleQuestionMark
        size={12}
        strokeWidth={2}
        className="cursor-help"
        style={{ color: '#93c5fd' }}
        aria-label="What counts as a result"
      />
      <div
        className="pointer-events-none absolute right-0 top-full z-10 mt-2 w-72 rounded-lg border bg-white p-2.5 text-[11px] leading-relaxed shadow opacity-0 translate-y-1 transition-all duration-150 group-hover:opacity-100 group-hover:translate-y-0"
        style={{ borderColor: '#dbeafe', color: '#1f2937' }}
      >
        Results is the number of qualified channels saved for that search term after your batch filters (subs, region,
        uploads, views). It matches how many leads in the table below are attributed to that term.
      </div>
    </span>
  )
}

interface LeadsTableSectionProps {
  leadsData: {
    leads: Array<{
      _id: string
      searchTermId?: string
      channelName?: string
      channelUrl?: string
      email?: string | null
      subscribers?: number
      score?: number
      emailStatus?: string
    }>
    total: number
  } | undefined
  terms: SearchTermItem[]
  isLoading: boolean
  isError: boolean
  error: unknown
  page: number
  pageSize: number
  onPrev: () => void
  onNext: () => void
}

function LeadsTableSection({
  leadsData,
  terms,
  isLoading,
  isError,
  error,
  page,
  pageSize,
  onPrev,
  onNext,
}: LeadsTableSectionProps) {
  const rows = leadsData?.leads ?? []
  const fillerRowCount = Math.max(0, pageSize - rows.length)
  const termLabelById = Object.fromEntries(terms.map((t) => [t._id, t.term]))

  return (
    <div className="flex flex-col rounded-xl border" style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}>
      <div
        className="grid grid-cols-12 gap-2 border-b px-4 py-2 text-[11px] font-semibold uppercase tracking-wide"
        style={{
          borderColor: 'rgba(37,99,235,0.2)',
          color: 'rgba(255,255,255,0.65)',
          background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 60%, #0a0f1e 100%)',
        }}
      >
        <div className="col-span-3">Channel</div>
        <div className="col-span-3">Search term</div>
        <div className="col-span-2">Email</div>
        <div className="col-span-2">Subscribers</div>
        <div className="col-span-1">
          <span className="inline-flex items-center gap-1">
            Score
            <ScoreTooltipIcon />
          </span>
        </div>
        <div className="col-span-1">Status</div>
      </div>
      <div>
        {isLoading ? (
          <p className="px-4 py-4 text-sm" style={{ color: '#6b7280' }}>
            Loading leads...
          </p>
        ) : isError ? (
          <p className="px-4 py-4 text-sm" style={{ color: '#be123c' }}>
            {getApiErrorMessage(error)}
          </p>
        ) : !leadsData || leadsData.leads.length === 0 ? (
          <p className="px-4 py-4 text-sm" style={{ color: '#6b7280' }}>
            No leads yet.
          </p>
        ) : (
          <div className="divide-y" style={{ borderColor: '#f3f4f6' }}>
            {rows.map((lead) => (
              <div key={lead._id} className="grid h-8 grid-cols-12 gap-2 px-4 text-sm items-center">
                <div className="col-span-3 truncate" style={{ color: '#111827' }}>
                  {lead.channelUrl ? (
                    <a
                      href={lead.channelUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline"
                      style={{ color: '#2563eb' }}
                    >
                      {lead.channelName ?? lead.channelUrl}
                    </a>
                  ) : (
                    lead.channelName ?? '—'
                  )}
                </div>
                <div
                  className="col-span-3 truncate"
                  title={lead.searchTermId ? termLabelById[lead.searchTermId] : undefined}
                  style={{ color: '#6b7280' }}
                >
                  {lead.searchTermId ? termLabelById[lead.searchTermId] ?? '—' : '—'}
                </div>
                <div className="col-span-2 truncate" style={{ color: '#6b7280' }}>
                  {lead.email ?? '—'}
                </div>
                <div className="col-span-2 tabular-nums" style={{ color: '#6b7280' }}>
                  {lead.subscribers != null ? lead.subscribers.toLocaleString() : '—'}
                </div>
                <div className="col-span-1 tabular-nums" style={{ color: '#6b7280' }}>
                  {lead.score ?? '—'}
                </div>
                <div className="col-span-1 truncate" style={{ color: '#6b7280' }}>
                  {lead.emailStatus ?? 'unknown'}
                </div>
              </div>
            ))}
            {Array.from({ length: fillerRowCount }).map((_, idx) => (
              <div
                key={`empty-${idx}`}
                className="grid h-8 grid-cols-12 gap-2 px-4 items-center text-sm"
              >
                <div className="col-span-12" style={{ color: '#e5e7eb' }}>
                  &nbsp;
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="flex items-center justify-between border-t px-4 py-2" style={{ borderColor: '#e5e7eb' }}>
        <span className="text-xs" style={{ color: '#6b7280' }}>
          Total {leadsData?.total ?? 0} leads
        </span>
        {leadsData && leadsData.total > pageSize && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onPrev}
              disabled={page <= 1}
              className="rounded border px-2.5 py-1 text-xs disabled:opacity-50"
              style={{ borderColor: '#e5e7eb' }}
            >
              Prev
            </button>
            <span className="text-xs" style={{ color: '#6b7280' }}>
              Page {page}
            </span>
            <button
              type="button"
              onClick={onNext}
              disabled={page * pageSize >= leadsData.total}
              className="rounded border px-2.5 py-1 text-xs disabled:opacity-50"
              style={{ borderColor: '#e5e7eb' }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value, compact = false }: { label: string; value: string; compact?: boolean }) {
  return (
    <div>
      <p className={`${compact ? 'text-[10px]' : 'text-xs'} font-medium uppercase tracking-wide`} style={{ color: '#6b7280' }}>
        {label}
      </p>
      <p className={`${compact ? 'mt-0.5 text-base' : 'mt-1 text-lg'} font-semibold tabular-nums`} style={{ color: '#0a0f1e' }}>
        {value}
      </p>
    </div>
  )
}

function ScoreTooltipIcon() {
  return (
    <span className="group relative inline-flex">
      <CircleQuestionMark
        size={14}
        strokeWidth={2}
        className="cursor-help"
        style={{ color: '#93c5fd' }}
        aria-label="Score details"
      />
      <div
        className="pointer-events-none absolute right-0 top-full z-10 mt-2 w-85 rounded-lg border bg-white p-3 text-[11px] leading-relaxed shadow opacity-0 translate-y-1 transition-all duration-150 group-hover:opacity-100 group-hover:translate-y-0"
        style={{ borderColor: '#dbeafe', color: '#1f2937' }}
      >
        <div className="mb-1 font-semibold" style={{ color: '#1e3a8a' }}>
          Score: what it means
        </div>
        <div className="mb-2">
          Score is an internal lead quality signal used to prioritize outreach. Higher score means better outreach priority.
        </div>
        <div className="mb-2">
          It combines three behaviors:
          <br />1) Recent posting activity (last 30 days) gets the strongest weight.
          <br />2) Subscriber size contributes with a logarithmic scale, so very large channels do not dominate unfairly.
          <br />3) Average video views add a lighter performance boost.
        </div>
        <div style={{ color: '#6b7280' }}>
          Only channels that already pass your batch filters (subs, country, minimum uploads, minimum avg views) are scored. Final score is rounded to 2 decimals.
        </div>
      </div>
    </span>
  )
}
