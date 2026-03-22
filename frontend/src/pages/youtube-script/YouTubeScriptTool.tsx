import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { BatchCard } from '@/components/youtube-script/BatchCard'
import { CreateBatchForm } from '@/components/youtube-script/CreateBatchForm'
import { DailyCreditMeter } from '@/components/youtube-script/DailyCreditMeter'
import { DailyLockNotice } from '@/components/youtube-script/DailyLockNotice'
import { useYouTubeScript } from '@/hooks/useYouTubeScript'

type Tab = 'list' | 'create'

export function YouTubeScriptTool() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('list')

  const {
    batches,
    addBatch,
    dailyCreditsUsed,
    creditsRemaining,
    creditUsagePercent,
    dailyCreditLimit,
    isDailyLocked,
    todaysBatchName,
  } = useYouTubeScript()

  function handleCreated() {
    navigate('/youtube-script', { replace: true })
    setTab('list')
  }

  return (
    <AppShell breadcrumb="YouTube Script">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#0a0f1e' }}>
              YouTube Script Automation
            </h1>
            <p className="mt-1 max-w-2xl text-sm leading-relaxed" style={{ color: '#6b7280' }}>
              Find channels from search terms and collect contact emails. Processing respects the daily YouTube
              API quota and can span multiple days.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setTab('create')}
            className="shrink-0 rounded-lg px-4 py-2 text-sm font-semibold text-white"
            style={{
              background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
              boxShadow: '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)',
            }}
          >
            + New Batch
          </button>
        </div>

        <div className="mb-6 border-b" style={{ borderColor: '#e5e7eb' }}>
          <div className="flex gap-6">
            {(
              [
                ['list', 'My Batches'],
                ['create', 'Create Batch'],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className="relative pb-3 text-sm font-medium"
                style={{
                  color: tab === id ? '#2563eb' : '#6b7280',
                }}
              >
                {label}
                {tab === id && (
                  <span
                    className="absolute inset-x-0 bottom-0 h-0.5 rounded-full"
                    style={{ background: 'linear-gradient(90deg, #2563eb, #1d4ed8)' }}
                  />
                )}
              </button>
            ))}
          </div>
        </div>

        {tab === 'list' && (
          <div className="space-y-4">
            <DailyCreditMeter
              dailyCreditsUsed={dailyCreditsUsed}
              creditsRemaining={creditsRemaining}
              creditUsagePercent={creditUsagePercent}
              dailyCreditLimit={dailyCreditLimit}
            />

            {isDailyLocked && todaysBatchName && (
              <DailyLockNotice batchName={todaysBatchName} />
            )}

            <div>
              <h2 className="mb-3 text-sm font-semibold" style={{ color: '#111827' }}>
                Active batches
              </h2>
              {batches.length === 0 ? (
                <div
                  className="rounded-xl border px-5 py-10 text-center"
                  style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}
                >
                  <p className="text-sm" style={{ color: '#6b7280' }}>
                    No batches yet.{' '}
                    <button
                      type="button"
                      onClick={() => setTab('create')}
                      className="font-semibold underline-offset-2 hover:underline"
                      style={{ color: '#2563eb' }}
                    >
                      Create your first batch
                    </button>
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                  {batches.map((b) => (
                    <BatchCard
                      key={b.id}
                      name={b.name}
                      keyword={b.keyword}
                      totalTerms={b.totalTerms}
                      processedTerms={b.processedTerms}
                      status={b.status}
                      createdAt={b.createdAt}
                      onClick={() => navigate(`/youtube-script/batch/${b.id}`)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {tab === 'create' && (
          <CreateBatchForm
            onCancel={() => setTab('list')}
            onCreated={handleCreated}
            onSubmitBatch={(payload) => {
              addBatch(payload)
            }}
          />
        )}
      </div>
    </AppShell>
  )
}
