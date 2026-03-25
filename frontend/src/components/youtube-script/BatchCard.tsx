type BatchStatus = 'queued' | 'running' | 'paused' | 'completed' | 'finalized' | 'failed'

interface BatchCardProps {
  name: string
  keyword: string
  totalTerms: number
  processedTerms: number
  status: BatchStatus
  createdAt: string
  onClick: () => void
  onTrigger?: () => void
  isTriggering?: boolean
}

function StatusBadge({ status }: { status: BatchStatus }) {
  const map: Record<
    BatchStatus,
    { label: string; bg: string; border: string; color: string }
  > = {
    running: {
      label: 'Running today',
      bg: 'rgba(37,99,235,0.08)',
      border: 'rgba(37,99,235,0.35)',
      color: '#1d4ed8',
    },
    paused: {
      label: 'Paused — continue tomorrow',
      bg: '#fffbeb',
      border: '#fcd34d',
      color: '#b45309',
    },
    completed: {
      label: 'Completed',
      bg: '#f0fdf4',
      border: '#bbf7d0',
      color: '#15803d',
    },
    finalized: {
      label: 'Finalized',
      bg: '#eff6ff',
      border: '#93c5fd',
      color: '#1d4ed8',
    },
    queued: {
      label: 'Queued',
      bg: '#f9fafb',
      border: '#e5e7eb',
      color: '#6b7280',
    },
    failed: {
      label: 'Failed',
      bg: '#fff1f2',
      border: '#fecdd3',
      color: '#be123c',
    },
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

export function BatchCard({
  name,
  keyword,
  totalTerms,
  processedTerms,
  status,
  createdAt,
  onClick,
  onTrigger,
  isTriggering = false,
}: BatchCardProps) {
  const pct = totalTerms > 0 ? Math.round((processedTerms / totalTerms) * 100) : 0

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-xl p-4 text-left transition-shadow"
      style={{
        border: '1px solid #e5e7eb',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(37,99,235,0.1)'
        e.currentTarget.style.borderColor = 'rgba(37,99,235,0.25)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)'
        e.currentTarget.style.borderColor = '#e5e7eb'
      }}
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold" style={{ color: '#0a0f1e' }}>
            {name}
          </p>
          <p className="mt-0.5 text-sm" style={{ color: '#6b7280' }}>
            Keyword: <span style={{ color: '#111827' }}>{keyword}</span>
          </p>
          <p className="mt-1 text-xs" style={{ color: '#9ca3af' }}>
            Created {new Date(createdAt).toLocaleString()}
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      {status === 'completed' || status === 'finalized' ? (
        <div className="flex items-center justify-between gap-2 text-sm">
          <span style={{ color: '#6b7280' }}>
            {processedTerms} of {totalTerms} terms processed
          </span>
          <span className="font-semibold" style={{ color: status === 'finalized' ? '#1d4ed8' : '#15803d' }}>
            {status === 'finalized' ? 'Ready to export' : 'Needs finalization'}
          </span>
        </div>
      ) : (
        <>
          <div className="mb-2 flex items-center justify-between text-sm">
            <span style={{ color: '#6b7280' }}>
              {processedTerms} of {totalTerms} terms processed
            </span>
            <span className="font-medium tabular-nums" style={{ color: '#111827' }}>
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
          {onTrigger && (
            <div className="mt-3 flex justify-end">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onTrigger()
                }}
                disabled={isTriggering}
                className="rounded-lg px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                style={{ background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' }}
              >
                {isTriggering ? 'Triggering...' : 'Trigger batch'}
              </button>
            </div>
          )}
        </>
      )}
    </button>
  )
}
