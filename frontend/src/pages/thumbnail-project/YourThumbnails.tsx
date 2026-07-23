import { useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, FolderOpen } from 'lucide-react'
import type { FolderPublic, ThumbnailJobPublic } from '@/client'
import { useThumbnailListInfiniteQuery } from '@/hooks/api/useThumbnailApi'
import { useFolderListQuery } from '@/hooks/api/useFolderApi'
import { ThumbnailDetailModal } from './ThumbnailDetailModal'

// Unfoldered thumbnails (folder_id === null) and any whose folder no longer
// resolves are funnelled into the team's "Testing" folder — matched by name so
// they merge with thumbnails explicitly created inside it, rather than forming a
// second, separate bucket.
const TESTING_FOLDER_NAME = 'testing'

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

function ThumbnailCard({
  item,
  onOpen,
}: {
  item: ThumbnailJobPublic
  onOpen: (id: string) => void
}) {
  return (
    <button
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
      onClick={() => onOpen(item.id)}
    >
      <div
        className="w-40 shrink-0 bg-black relative flex items-center justify-center p-1 border-r"
        style={{ borderColor: '#e5e7eb' }}
      >
        {item.result_url || item.candidate_urls?.[0] ? (
          <img
            src={item.result_url ?? item.candidate_urls![0]}
            alt={item.title ?? 'Thumbnail'}
            className="w-full h-full object-cover rounded shadow-sm opacity-90 transition-opacity hover:opacity-100"
          />
        ) : (
          <div className="text-[10px] text-center px-2 text-gray-400 leading-tight">
            {item.status}
          </div>
        )}
        {!item.result_url && item.candidate_urls?.length ? (
          <span
            className="absolute bottom-1 left-1 right-1 rounded px-1.5 py-0.5 text-center text-[9px] font-semibold uppercase"
            style={{ backgroundColor: 'rgba(180,83,9,0.85)', color: '#fff' }}
          >
            Pick one
          </span>
        ) : null}
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
  )
}

type FolderSection = {
  key: string
  name: string
  isTesting: boolean
  jobs: ThumbnailJobPublic[]
}

/**
 * Group loaded jobs into one section per folder, ordered folder-list first and
 * Testing last. Every existing folder is shown (even when empty) so the team's
 * organisation is visible; unfoldered thumbnails collapse into Testing.
 */
function buildSections(
  folders: FolderPublic[],
  jobs: ThumbnailJobPublic[],
): FolderSection[] {
  const testingFolder = folders.find(
    (f) => f.name.trim().toLowerCase() === TESTING_FOLDER_NAME,
  )
  const knownIds = new Set(folders.map((f) => f.id))

  const byFolder = new Map<string, ThumbnailJobPublic[]>()
  const testingJobs: ThumbnailJobPublic[] = []

  for (const job of jobs) {
    const fid = job.folder_id
    // No folder, unresolved folder, or the Testing folder itself → Testing bucket.
    if (!fid || !knownIds.has(fid) || (testingFolder && fid === testingFolder.id)) {
      testingJobs.push(job)
      continue
    }
    const bucket = byFolder.get(fid)
    if (bucket) bucket.push(job)
    else byFolder.set(fid, [job])
  }

  const sections: FolderSection[] = folders
    .filter((f) => !testingFolder || f.id !== testingFolder.id)
    .map((f) => ({
      key: f.id,
      name: f.name,
      isTesting: false,
      jobs: byFolder.get(f.id) ?? [],
    }))

  sections.push({
    key: testingFolder?.id ?? '__testing__',
    name: testingFolder?.name ?? 'Testing',
    isTesting: true,
    jobs: testingJobs,
  })

  return sections
}

export function YourThumbnails() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())

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

  const { data: folderData } = useFolderListQuery()

  // Grouping by folder needs the full set, not just the first page — otherwise a
  // folder's section would look emptier than it is. Auto-advance through the
  // cursor pages until they're exhausted.
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const jobs = useMemo(() => data?.pages.flatMap((p) => p.jobs) ?? [], [data])
  const folders = useMemo(() => folderData?.folders ?? [], [folderData])
  const sections = useMemo(() => buildSections(folders, jobs), [folders, jobs])

  const loadError = isError
    ? error instanceof Error
      ? error.message
      : 'Failed to load thumbnails'
    : null
  const stillLoadingAll = isLoading || hasNextPage || isFetchingNextPage

  function toggle(key: string) {
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

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
        <div className="space-y-8">
          {sections.map((section) => {
            const isCollapsed = collapsed.has(section.key)
            return (
              <section key={section.key}>
                <button
                  type="button"
                  onClick={() => toggle(section.key)}
                  className="flex w-full items-center gap-2 border-b pb-2 mb-4 text-left"
                  style={{ borderColor: '#e5e7eb' }}
                >
                  {isCollapsed ? (
                    <ChevronRight className="w-4 h-4 shrink-0" style={{ color: '#9ca3af' }} />
                  ) : (
                    <ChevronDown className="w-4 h-4 shrink-0" style={{ color: '#9ca3af' }} />
                  )}
                  <FolderOpen
                    className="w-4 h-4 shrink-0"
                    style={{ color: section.isTesting ? '#9ca3af' : '#2563eb' }}
                  />
                  <h2 className="text-sm font-semibold" style={{ color: '#0a0f1e' }}>
                    {section.name}
                  </h2>
                  {section.isTesting && (
                    <span className="text-xs" style={{ color: '#9ca3af' }}>
                      unfiled
                    </span>
                  )}
                  <span
                    className="ml-1 rounded-full px-2 py-0.5 text-[11px] font-medium"
                    style={{ backgroundColor: '#f3f4f6', color: '#6b7280' }}
                  >
                    {section.jobs.length}
                  </span>
                </button>

                {!isCollapsed &&
                  (section.jobs.length === 0 ? (
                    <p className="text-sm pb-2 pl-6" style={{ color: '#9ca3af' }}>
                      No thumbnails in this folder yet.
                    </p>
                  ) : (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-2">
                      {section.jobs.map((item) => (
                        <ThumbnailCard key={item.id} item={item} onOpen={setSelectedJobId} />
                      ))}
                    </div>
                  ))}
              </section>
            )
          })}

          {stillLoadingAll && !isLoading && (
            <p className="text-center text-xs" style={{ color: '#9ca3af' }}>
              Loading all thumbnails…
            </p>
          )}
        </div>
      )}

      {selectedJobId && (
        <ThumbnailDetailModal jobId={selectedJobId} onClose={() => setSelectedJobId(null)} />
      )}
    </>
  )
}
