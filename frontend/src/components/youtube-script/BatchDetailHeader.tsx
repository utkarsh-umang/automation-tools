import type { BatchDetail, BatchStatus } from '@/hooks/api/useYoutubeApi'

function StatusBadge({ status }: { status: BatchStatus }) {
  const map: Record<BatchStatus, { label: string; bg: string; border: string; color: string }> = {
    running: { label: 'Running', bg: 'rgba(37,99,235,0.08)', border: 'rgba(37,99,235,0.35)', color: '#1d4ed8' },
    paused: { label: 'Paused', bg: '#fffbeb', border: '#fcd34d', color: '#b45309' },
    completed: { label: 'Completed', bg: '#f0fdf4', border: '#bbf7d0', color: '#15803d' },
    queued: { label: 'Queued', bg: '#f9fafb', border: '#e5e7eb', color: '#6b7280' },
    failed: { label: 'Failed', bg: '#fff1f2', border: '#fecdd3', color: '#be123c' },
  }
  const s = map[status]
  return (
    <span
      className="rounded px-2 py-0.5 text-xs font-semibold"
      style={{ backgroundColor: s.bg, border: `1px solid ${s.border}`, color: s.color }}
    >
      {s.label}
    </span>
  )
}

interface BatchDetailHeaderProps {
  batch: BatchDetail
  onBack: () => void
}

export function BatchDetailHeader({ batch, onBack }: BatchDetailHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <button
          type="button"
          onClick={onBack}
          className="mb-3 inline-flex items-center gap-1.5 text-sm font-medium"
          style={{ color: '#2563eb' }}
        >
          <span aria-hidden>←</span> Back to batches
        </button>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-bold" style={{ color: '#0a0f1e' }}>
            {batch.name}
          </h1>
          <StatusBadge status={batch.status} />
        </div>
        <p className="mt-1 text-sm" style={{ color: '#6b7280' }}>
          Keyword: <span style={{ color: '#111827' }}>{batch.keyword}</span>
          <span className="mx-2" style={{ color: '#d1d5db' }}>
            ·
          </span>
          {batch.totalTerms} terms
          <span className="mx-2" style={{ color: '#d1d5db' }}>
            ·
          </span>
          Created {new Date(batch.createdAt).toLocaleString()}
        </p>
      </div>
    </div>
  )
}
