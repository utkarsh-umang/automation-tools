import { useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { BatchDetailHeader } from '@/components/youtube-script/BatchDetailHeader'
import { useYouTubeScript } from '@/hooks/useYouTubeScript'

export function BatchDetailPage() {
  const { batchId } = useParams<{ batchId: string }>()
  const navigate = useNavigate()
  const { batches } = useYouTubeScript()

  const batch = useMemo(() => batches.find((b) => b.id === batchId), [batches, batchId])

  function goBack() {
    navigate('/youtube-script')
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
  const estDays = Math.ceil(remaining / 100)

  if (batch.status === 'paused') {
    return (
      <AppShell breadcrumb="YouTube Script">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <BatchDetailHeader batch={batch} onBack={goBack} />

          <div
            className="mb-6 flex gap-3 rounded-xl border px-4 py-3"
            style={{
              backgroundColor: '#fffbeb',
              borderColor: '#fcd34d',
            }}
          >
            <svg className="mt-0.5 h-5 w-5 shrink-0" style={{ color: '#d97706' }} fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-sm leading-relaxed" style={{ color: '#92400e' }}>
              This batch is paused — another batch is already running today. Come back tomorrow to continue
              processing the remaining <strong>{remaining}</strong> terms.
            </p>
          </div>

          <div
            className="grid grid-cols-1 gap-3 rounded-xl border p-4 sm:grid-cols-3"
            style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}
          >
            <Stat label="Terms processed" value={String(batch.processedTerms)} />
            <Stat label="Terms remaining" value={String(remaining)} />
            <Stat label="Est. days to complete" value={String(estDays)} />
          </div>

          <div className="mt-6">
            <p className="mb-2 text-sm font-medium" style={{ color: '#111827' }}>
              Overall progress
            </p>
            <div className="h-3 w-full max-w-xl overflow-hidden rounded-full" style={{ backgroundColor: '#f3f4f6' }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${pct}%`,
                  background: 'linear-gradient(90deg, #2563eb, #1d4ed8)',
                }}
              />
            </div>
            <p className="mt-1 text-xs tabular-nums" style={{ color: '#6b7280' }}>
              {pct}% complete
            </p>
          </div>
        </div>
      </AppShell>
    )
  }

  if (batch.status === 'completed') {
    return (
      <AppShell breadcrumb="YouTube Script">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <BatchDetailHeader batch={batch} onBack={goBack} />

          <div
            className="mb-6 flex gap-3 rounded-xl border px-4 py-3"
            style={{
              backgroundColor: '#f0fdf4',
              borderColor: '#bbf7d0',
            }}
          >
            <svg className="mt-0.5 h-5 w-5 shrink-0" style={{ color: '#15803d' }} fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-sm font-medium" style={{ color: '#15803d' }}>
              All {batch.totalTerms} search terms have been processed. Export is available below.
            </p>
          </div>

          <div
            className="mb-6 grid grid-cols-1 gap-3 rounded-xl border p-4 sm:grid-cols-3"
            style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}
          >
            <Stat label="Terms processed" value={String(batch.processedTerms)} />
            <Stat label="Channels found" value={String(batch.channelsFound ?? '—')} />
            <Stat label="Emails extracted" value={String(batch.emailsExtracted ?? '—')} />
          </div>

          <div
            className="mb-6 rounded-lg border px-3 py-2.5 text-sm"
            style={{
              backgroundColor: '#eff6ff',
              borderColor: 'rgba(37,99,235,0.25)',
              color: '#1e3a8a',
            }}
          >
            Export functionality is coming soon — results will be downloadable as CSV.
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-lg px-4 py-2.5 text-sm font-semibold text-white opacity-60"
              style={{
                background: 'linear-gradient(135deg, #93c5fd 0%, #60a5fa 100%)',
              }}
            >
              Export CSV (coming soon)
            </button>
            <button
              type="button"
              onClick={goBack}
              className="rounded-lg px-4 py-2.5 text-sm font-medium"
              style={{
                border: '1px solid #e5e7eb',
                color: '#374151',
                backgroundColor: '#ffffff',
              }}
            >
              ← Back to batches
            </button>
          </div>
        </div>
      </AppShell>
    )
  }

  if (batch.status === 'queued') {
    return (
      <AppShell breadcrumb="YouTube Script">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <BatchDetailHeader batch={batch} onBack={goBack} />
          <div
            className="rounded-xl border px-5 py-8"
            style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}
          >
            <p className="text-sm leading-relaxed" style={{ color: '#6b7280' }}>
              This batch is <strong style={{ color: '#111827' }}>queued</strong>. Trigger it from the batch list
              when you are ready — remember only one batch can run per day.
            </p>
          </div>
        </div>
      </AppShell>
    )
  }

  // running (in progress)
  const rows = batch.termRows ?? []

  return (
    <AppShell breadcrumb="YouTube Script">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <BatchDetailHeader batch={batch} onBack={goBack} />

        <div
          className="mb-6 grid grid-cols-1 gap-3 rounded-xl border p-4 sm:grid-cols-3"
          style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}
        >
          <Stat label="Terms processed" value={String(batch.processedTerms)} />
          <Stat
            label="Currently running"
            value={String(rows.filter((r) => r.status === 'running').length ? 1 : 0)}
          />
          <Stat label="Terms remaining" value={String(remaining)} />
        </div>

        <div className="mb-6">
          <div className="mb-2 flex items-center justify-between gap-2">
            <p className="text-sm font-medium" style={{ color: '#111827' }}>
              Batch progress
            </p>
            <span className="text-sm tabular-nums font-semibold" style={{ color: '#2563eb' }}>
              {pct}%
            </span>
          </div>
          <div className="h-3 w-full overflow-hidden rounded-full" style={{ backgroundColor: '#f3f4f6' }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${pct}%`,
                background: 'linear-gradient(90deg, #2563eb, #1d4ed8)',
              }}
            />
          </div>
        </div>

        <div
          className="overflow-hidden rounded-xl border"
          style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}
        >
          <div
            className="grid grid-cols-12 gap-2 border-b px-4 py-3 text-xs font-semibold uppercase tracking-wide"
            style={{ borderColor: '#e5e7eb', color: '#6b7280' }}
          >
            <div className="col-span-5">Search term</div>
            <div className="col-span-3">Credits used</div>
            <div className="col-span-4 text-right sm:text-left">Status</div>
          </div>
          <div className="divide-y" style={{ borderColor: '#f3f4f6' }}>
            {rows.map((row, i) => (
              <div key={`${i}-${row.term}`} className="grid grid-cols-12 gap-2 px-4 py-3 text-sm">
                <div className="col-span-5 break-words" style={{ color: '#111827' }}>
                  {row.term}
                </div>
                <div className="col-span-3 tabular-nums" style={{ color: '#6b7280' }}>
                  {row.creditsUsed == null ? '—' : row.creditsUsed}
                </div>
                <div className="col-span-4">
                  <RowStatus status={row.status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide" style={{ color: '#6b7280' }}>
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold tabular-nums" style={{ color: '#0a0f1e' }}>
        {value}
      </p>
    </div>
  )
}

function RowStatus({ status }: { status: 'done' | 'running' | 'pending' }) {
  if (status === 'done') {
    return (
      <span className="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" style={{ background: '#f0fdf4', color: '#15803d' }}>
        Done
      </span>
    )
  }
  if (status === 'running') {
    return (
      <span className="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" style={{ background: 'rgba(37,99,235,0.1)', color: '#1d4ed8' }}>
        Running
      </span>
    )
  }
  return (
    <span className="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" style={{ background: '#f9fafb', color: '#6b7280' }}>
      Pending
    </span>
  )
}
