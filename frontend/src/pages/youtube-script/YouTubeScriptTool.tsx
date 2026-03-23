import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { BatchCard } from '@/components/youtube-script/BatchCard'
import { CreateBatchForm } from '@/components/youtube-script/CreateBatchForm'
import { DailyCreditMeter } from '@/components/youtube-script/DailyCreditMeter'
import { DailyLockNotice } from '@/components/youtube-script/DailyLockNotice'
import {
  getApiErrorMessage,
  useBatchesQuery,
  useCreateBatchMutation,
  useCreditsTodayQuery,
  useTriggerBatchMutation,
  type BatchItem,
} from '@/hooks/api/useYoutubeApi'

type Tab = 'list' | 'create'

export function YouTubeScriptTool() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('list')
  const batchesQuery = useBatchesQuery()
  const creditsQuery = useCreditsTodayQuery(10_000)
  const createMutation = useCreateBatchMutation()
  const triggerMutation = useTriggerBatchMutation()

  const batches = batchesQuery.data ?? []
  const credits = creditsQuery.data
  const activeBatch = credits?.activeBatchId ? batches.find((b) => b._id === credits.activeBatchId) : null

  function handleCreated() {
    navigate('/youtube-script', { replace: true })
    setTab('list')
  }

  async function handleCreate(payload: { name: string; keyword: string; termsRaw: string }) {
    await createMutation.mutateAsync({
      name: payload.name,
      keyword: payload.keyword,
      terms: payload.termsRaw,
      filters: {
        minSubs: 0,
        maxSubs: 1_000_000,
        minUploadsLast30d: 1,
        minAvgViews: 0,
        excludeCountries: ['IN'],
        region: 'US',
      },
    })
  }

  function canTrigger(batch: BatchItem): boolean {
    if (batch.status !== 'queued' && batch.status !== 'paused') return false
    if (!credits?.activeBatchId) return true
    return credits.activeBatchId === batch._id
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
          {tab === 'list' && (
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
          )}
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
            {credits ? (
              <DailyCreditMeter
                dailyCreditsUsed={credits.used}
                creditsRemaining={credits.remaining}
                creditUsagePercent={credits.limit > 0 ? (credits.used / credits.limit) * 100 : 0}
                dailyCreditLimit={credits.limit}
              />
            ) : (
              <div className="rounded-xl border px-4 py-4 text-sm" style={{ borderColor: '#e5e7eb' }}>
                {creditsQuery.isLoading ? 'Loading credits...' : 'Unable to load credits.'}
              </div>
            )}

            {credits?.activeBatchId && (
              <DailyLockNotice batchName={activeBatch?.name ?? 'Another batch'} />
            )}

            <div>
              <h2 className="mb-3 text-sm font-semibold" style={{ color: '#111827' }}>
                Active batches
              </h2>
              {batchesQuery.isLoading ? (
                <div className="rounded-xl border px-5 py-10 text-center" style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}>
                  <p className="text-sm" style={{ color: '#6b7280' }}>
                    Loading batches...
                  </p>
                </div>
              ) : batchesQuery.isError ? (
                <div className="rounded-xl border px-5 py-10 text-center" style={{ borderColor: '#fecdd3', backgroundColor: '#fff1f2' }}>
                  <p className="text-sm" style={{ color: '#be123c' }}>
                    {getApiErrorMessage(batchesQuery.error)}
                  </p>
                </div>
              ) : batches.length === 0 ? (
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
                      key={b._id}
                      name={b.name}
                      keyword={b.keyword}
                      totalTerms={b.totalTerms}
                      processedTerms={b.processedTerms}
                      status={b.status}
                      createdAt={b.createdAt}
                      onClick={() => navigate(`/youtube-script/batch/${b._id}`)}
                      onTrigger={
                        canTrigger(b)
                          ? () => {
                              triggerMutation.mutate(b._id)
                            }
                          : undefined
                      }
                      isTriggering={triggerMutation.isPending && triggerMutation.variables === b._id}
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
            onSubmitBatch={handleCreate}
            isSubmitting={createMutation.isPending}
            errorMessage={createMutation.isError ? getApiErrorMessage(createMutation.error) : null}
          />
        )}
      </div>
    </AppShell>
  )
}
