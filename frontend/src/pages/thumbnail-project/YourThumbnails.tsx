import { useMemo, useState } from 'react'
import type { ThumbnailJobPublic } from '@/client'
import { useThumbnailListInfiniteQuery } from '@/hooks/api/useThumbnailApi'
import { ThumbnailDetailModal } from './ThumbnailDetailModal'

function formatWhen(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}

function statusBadgeStyle(status: string) {
  const s = status.toLowerCase()
  if (s === 'completed') {
    return {
      backgroundColor: '#f0fdf4',
      border: '1px solid #bbf7d0',
      color: '#15803d',
    }
  }
  if (s === 'failed') {
    return {
      backgroundColor: '#fef2f2',
      border: '1px solid #fecaca',
      color: '#b91c1c',
    }
  }
  return {
    backgroundColor: '#fffbeb',
    border: '1px solid #fde68a',
    color: '#b45309',
  }
}

export function YourThumbnails() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useThumbnailListInfiniteQuery(20)

  const jobs = useMemo(() => data?.pages.flatMap((p) => p.jobs) ?? [], [data])
  const loadError = isError ? (error instanceof Error ? error.message : 'Failed to load thumbnails') : null

  return (
    <>
      {isLoading && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-36 rounded-xl animate-pulse"
              style={{ backgroundColor: '#f3f4f6', border: '1px solid #e5e7eb' }}
            />
          ))}
        </div>
      )}

      {loadError && !isLoading && (
        <div
          className="rounded-xl p-6 text-sm"
          style={{ color: '#b91c1c', backgroundColor: '#fef2f2', border: '1px solid #fecaca' }}
        >
          {loadError}{' '}
          <button type="button" className="underline font-medium" onClick={() => void refetch()}>
            Retry
          </button>
        </div>
      )}

      {!isLoading && !loadError && jobs.length === 0 && (
        <p className="text-sm py-8 text-center" style={{ color: '#6b7280' }}>
          No thumbnails yet. Create one to generate your first asset.
        </p>
      )}

      {!isLoading && !loadError && jobs.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-2">
            {jobs.map((item: ThumbnailJobPublic) => (
              <button
                key={item.id}
                type="button"
                className="w-full text-left rounded-xl overflow-hidden transition-shadow flex h-36"
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
                onClick={() => setSelectedJobId(item.id)}
              >
                <div
                  className="w-40 shrink-0 bg-black relative flex items-center justify-center p-1 border-r"
                  style={{ borderColor: '#e5e7eb' }}
                >
                  {item.result_url ? (
                    <img
                      src={item.result_url}
                      alt={item.title ?? 'Thumbnail'}
                      className="w-full h-full object-cover rounded shadow-sm opacity-90 transition-opacity hover:opacity-100"
                    />
                  ) : (
                    <div className="text-[10px] text-center px-2 text-gray-400 leading-tight">
                      {item.status}
                    </div>
                  )}
                </div>
                <div className="p-4 flex flex-col justify-between flex-1 min-w-0">
                  <div>
                    <div className="flex justify-between items-start mb-1 gap-2">
                      <h3 className="truncate text-base font-semibold" style={{ color: '#0a0f1e' }}>
                        {item.title ?? 'Untitled'}
                      </h3>
                      <span
                        className="rounded px-2 py-0.5 text-[10px] font-semibold shrink-0 uppercase"
                        style={statusBadgeStyle(item.status)}
                      >
                        {item.status}
                      </span>
                    </div>
                    <p className="line-clamp-2 text-sm leading-relaxed" style={{ color: '#6b7280' }}>
                      {item.error ?? item.creative_comments ?? item.model ?? '—'}
                    </p>
                  </div>
                  <div className="mt-2 text-xs" style={{ color: '#9ca3af' }}>
                    Updated {formatWhen(item.updated_at)}
                  </div>
                </div>
              </button>
            ))}
          </div>

          {hasNextPage && (
            <div className="mt-6 flex justify-center">
              <button
                type="button"
                className="rounded-lg px-4 py-2 text-sm font-medium border"
                style={{ borderColor: '#e5e7eb', color: '#374151', backgroundColor: '#ffffff' }}
                disabled={isFetchingNextPage}
                onClick={() => void fetchNextPage()}
              >
                {isFetchingNextPage ? 'Loading…' : 'Load more'}
              </button>
            </div>
          )}
        </>
      )}

      {selectedJobId && (
        <ThumbnailDetailModal jobId={selectedJobId} onClose={() => setSelectedJobId(null)} />
      )}
    </>
  )
}
