import { useEffect, useState } from 'react'

export interface CreditKeyRow {
  id: string
  label: string
  used: number
  limit: number
  remaining: number
}

interface DailyCreditMeterProps {
  dailyCreditsUsed: number
  creditsRemaining: number
  creditUsagePercent: number
  dailyCreditLimit: number
  resetAt?: string
  /** Per-API-key usage when multiple keys are configured */
  keys?: CreditKeyRow[]
}

export function DailyCreditMeter({
  dailyCreditsUsed,
  creditsRemaining,
  creditUsagePercent,
  dailyCreditLimit,
  resetAt,
  keys = [],
}: DailyCreditMeterProps) {
  const highUsage = creditUsagePercent >= 80
  const barColor = highUsage ? '#f59e0b' : '#2563eb'
  const [nowMs, setNowMs] = useState(() => Date.now())

  useEffect(() => {
    const id = window.setInterval(() => setNowMs(Date.now()), 60_000)
    return () => window.clearInterval(id)
  }, [])

  function getResetCountdownLabel(): string | null {
    if (!resetAt) return null
    const resetMs = new Date(resetAt).getTime()
    if (Number.isNaN(resetMs)) return null
    const diffMs = Math.max(0, resetMs - nowMs)
    const totalMinutes = Math.floor(diffMs / 60_000)
    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60
    return `Resets in ${hours}h ${minutes}m`
  }

  const resetCountdownLabel = getResetCountdownLabel()

  return (
    <div
      className="rounded-xl px-4 py-4"
      style={{
        border: '1px solid #e5e7eb',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}
    >
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="text-sm font-semibold" style={{ color: '#0a0f1e' }}>
            YouTube API credits (today)
          </p>
          <p className="mt-0.5 text-xs" style={{ color: '#6b7280' }}>
            Resets daily · {dailyCreditLimit.toLocaleString()} credit limit (all keys)
          </p>
          {resetCountdownLabel && (
            <p className="mt-0.5 text-xs font-medium" style={{ color: '#2563eb' }}>
              {resetCountdownLabel}
            </p>
          )}
        </div>
        <div className="text-right text-sm">
          <span style={{ color: '#111827' }}>
            <strong>{dailyCreditsUsed.toLocaleString()}</strong> used
          </span>
          <span className="mx-2" style={{ color: '#d1d5db' }}>
            ·
          </span>
          <span style={{ color: '#6b7280' }}>{creditsRemaining.toLocaleString()} remaining</span>
        </div>
      </div>
      <div
        className="h-2.5 w-full overflow-hidden rounded-full"
        style={{ backgroundColor: '#f3f4f6' }}
      >
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${Math.min(100, creditUsagePercent)}%`,
            backgroundColor: barColor,
          }}
        />
      </div>

      {keys.length > 0 && (
        <div className="mt-4 space-y-2 border-t pt-3" style={{ borderColor: '#f3f4f6' }}>
          <p className="text-xs font-medium" style={{ color: '#6b7280' }}>
            Per key
          </p>
          {keys.map((k) => {
            const pct = k.limit > 0 ? Math.min(100, (k.used / k.limit) * 100) : 0
            const rowHigh = pct >= 80
            return (
              <div key={k.id}>
                <div className="mb-1 flex justify-between text-xs">
                  <span style={{ color: '#374151' }}>{k.label}</span>
                  <span style={{ color: '#6b7280' }}>
                    {k.used.toLocaleString()} / {k.limit.toLocaleString()} ({k.remaining.toLocaleString()} left)
                  </span>
                </div>
                <div
                  className="h-1.5 w-full overflow-hidden rounded-full"
                  style={{ backgroundColor: '#f3f4f6' }}
                >
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: rowHigh ? '#f59e0b' : '#93c5fd',
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
