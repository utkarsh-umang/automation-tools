import { useMemo, useState } from 'react'
import { ChevronLeft, Folder, FolderOpen, ImageOff } from 'lucide-react'
import type { FolderPublic, FolderSummary, ThumbnailJobPublic } from '@/client'
import { useThumbnailListInfiniteQuery } from '@/hooks/api/useThumbnailApi'
import { useFolderListQuery, useFolderSummaryQuery } from '@/hooks/api/useFolderApi'
import { ThumbnailDetailModal } from './ThumbnailDetailModal'

// Unfoldered thumbnails (folder_id === null) are funnelled into the team's
// "Testing" folder — matched by name so they merge with thumbnails explicitly
// created inside it, rather than forming a second, separate bucket.
const TESTING_FOLDER_NAME = 'testing'

const PAGE_SIZE = 24

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
    return { backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#15803d' }
  }
  if (s === 'failed') {
    return { backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c' }
  }
  return { backgroundColor: '#fffbeb', border: '1px solid #fde68a', color: '#b45309' }
}

/** One thumbnail lineage, represented by its latest iteration. */
function ThumbnailCard({
  item,
  onOpen,
}: {
  item: ThumbnailJobPublic
  onOpen: (id: string) => void
}) {
  const cover = item.result_url ?? item.candidate_urls?.[0] ?? null
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
        {cover ? (
          <img
            src={cover}
            alt={item.title ?? 'Thumbnail'}
            className="w-full h-full object-cover rounded shadow-sm opacity-90 transition-opacity hover:opacity-100"
          />
        ) : (
          <div className="text-[10px] text-center px-2 text-gray-400 leading-tight">
            {item.status}
          </div>
        )}
        {item.iteration > 1 ? (
          <span
            className="absolute top-1 left-1 rounded px-1.5 py-0.5 text-[9px] font-bold"
            style={{ backgroundColor: 'rgba(37,99,235,0.9)', color: '#fff' }}
            title={`Latest of ${item.iteration} versions — see full history inside`}
          >
            v{item.iteration}
          </span>
        ) : null}
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

type FolderTile = {
  key: string
  name: string
  count: number
  coverUrl: string | null
  isTesting: boolean
  // Query params to open this tile's contents.
  folderId: string | null
  includeUnfoldered: boolean
}

/**
 * Build the album grid: one tile per folder (folder-list ordered), Testing last.
 * The Testing tile merges the "testing" folder with every unfiled thumbnail
 * (folder_id === null), so counts and cover reflect both.
 */
function buildTiles(
  folders: FolderPublic[],
  summaries: FolderSummary[],
): FolderTile[] {
  const byFolder = new Map<string, FolderSummary>()
  let unfoldered: FolderSummary | undefined
  for (const s of summaries) {
    if (s.folder_id == null) unfoldered = s
    else byFolder.set(s.folder_id, s)
  }

  const testingFolder = folders.find(
    (f) => f.name.trim().toLowerCase() === TESTING_FOLDER_NAME,
  )

  const tiles: FolderTile[] = folders
    .filter((f) => !testingFolder || f.id !== testingFolder.id)
    .map((f) => {
      const sum = byFolder.get(f.id)
      return {
        key: f.id,
        name: f.name,
        count: sum?.count ?? 0,
        coverUrl: sum?.cover_url ?? null,
        isTesting: false,
        folderId: f.id,
        includeUnfoldered: false,
      }
    })

  const testingSum = testingFolder ? byFolder.get(testingFolder.id) : undefined
  tiles.push({
    key: testingFolder?.id ?? '__testing__',
    name: testingFolder?.name ?? 'Testing',
    count: (testingSum?.count ?? 0) + (unfoldered?.count ?? 0),
    coverUrl: testingSum?.cover_url ?? unfoldered?.cover_url ?? null,
    isTesting: true,
    folderId: testingFolder?.id ?? null,
    includeUnfoldered: true,
  })

  return tiles
}

function FolderCover({ tile, onOpen }: { tile: FolderTile; onOpen: (t: FolderTile) => void }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(tile)}
      className="group text-left rounded-2xl overflow-hidden transition-all"
      style={{ border: '1px solid #e5e7eb', backgroundColor: '#fff' }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(37,99,235,0.12)'
        e.currentTarget.style.borderColor = 'rgba(37,99,235,0.3)'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none'
        e.currentTarget.style.borderColor = '#e5e7eb'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
    >
      <div className="aspect-square w-full bg-black relative flex items-center justify-center">
        {tile.coverUrl ? (
          <img src={tile.coverUrl} alt={tile.name} className="w-full h-full object-cover" />
        ) : (
          <div className="flex flex-col items-center gap-2" style={{ color: '#4b5563' }}>
            {tile.isTesting ? (
              <Folder className="w-10 h-10" />
            ) : (
              <ImageOff className="w-10 h-10" />
            )}
            <span className="text-[11px]">Empty</span>
          </div>
        )}
        <span
          className="absolute top-2 right-2 rounded-full px-2 py-0.5 text-[11px] font-semibold"
          style={{ backgroundColor: 'rgba(0,0,0,0.6)', color: '#fff', backdropFilter: 'blur(4px)' }}
        >
          {tile.count}
        </span>
      </div>
      <div className="px-3 py-2.5 flex items-center gap-2 min-w-0">
        <FolderOpen
          className="w-4 h-4 shrink-0"
          style={{ color: tile.isTesting ? '#9ca3af' : '#2563eb' }}
        />
        <span className="truncate text-sm font-semibold" style={{ color: '#0a0f1e' }}>
          {tile.name}
        </span>
        {tile.isTesting ? (
          <span className="text-[11px] shrink-0" style={{ color: '#9ca3af' }}>
            unfiled
          </span>
        ) : null}
      </div>
    </button>
  )
}

function FolderGridSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className="rounded-2xl animate-pulse"
          style={{ backgroundColor: '#f3f4f6', border: '1px solid #e5e7eb', aspectRatio: '1 / 1.15' }}
        />
      ))}
    </div>
  )
}

/** The paginated contents of one opened folder. */
function FolderContents({
  tile,
  onBack,
  onOpenJob,
}: {
  tile: FolderTile
  onBack: () => void
  onOpenJob: (id: string) => void
}) {
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useThumbnailListInfiniteQuery(PAGE_SIZE, {
    folderId: tile.folderId,
    rootsOnly: true,
    includeUnfoldered: tile.includeUnfoldered,
  })

  const jobs = useMemo(() => data?.pages.flatMap((p) => p.jobs) ?? [], [data])
  const loadError = isError
    ? error instanceof Error
      ? error.message
      : 'Failed to load thumbnails'
    : null

  return (
    <div>
      <div className="flex items-center gap-3 mb-5">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-sm font-medium transition-colors"
          style={{ border: '1px solid #e5e7eb', color: '#374151', backgroundColor: '#fff' }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f9fafb')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#fff')}
        >
          <ChevronLeft className="w-4 h-4" />
          Folders
        </button>
        <div className="flex items-center gap-2 min-w-0">
          <FolderOpen
            className="w-5 h-5 shrink-0"
            style={{ color: tile.isTesting ? '#9ca3af' : '#2563eb' }}
          />
          <h2 className="truncate text-lg font-semibold" style={{ color: '#0a0f1e' }}>
            {tile.name}
          </h2>
          <span
            className="rounded-full px-2 py-0.5 text-[11px] font-medium"
            style={{ backgroundColor: '#f3f4f6', color: '#6b7280' }}
          >
            {tile.count}
          </span>
        </div>
      </div>

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
        <p className="text-sm py-10 text-center" style={{ color: '#9ca3af' }}>
          No thumbnails in this folder yet.
        </p>
      )}

      {!isLoading && !loadError && jobs.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {jobs.map((item) => (
              <ThumbnailCard key={item.id} item={item} onOpen={onOpenJob} />
            ))}
          </div>

          {hasNextPage ? (
            <div className="mt-6 flex justify-center">
              <button
                type="button"
                onClick={() => void fetchNextPage()}
                disabled={isFetchingNextPage}
                className="rounded-lg px-5 py-2 text-sm font-medium transition-colors disabled:opacity-60"
                style={{ border: '1px solid #d1d5db', color: '#374151', backgroundColor: '#fff' }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f9fafb')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#fff')}
              >
                {isFetchingNextPage ? 'Loading…' : 'Load more'}
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  )
}

export function YourThumbnails() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [openTile, setOpenTile] = useState<FolderTile | null>(null)

  const { data: folderData, isLoading: foldersLoading } = useFolderListQuery()
  const { data: summaryData, isLoading: summaryLoading } = useFolderSummaryQuery()

  const folders = useMemo(() => folderData?.folders ?? [], [folderData])
  const summaries = useMemo(() => summaryData?.summaries ?? [], [summaryData])
  const tiles = useMemo(() => buildTiles(folders, summaries), [folders, summaries])

  const gridLoading = foldersLoading || summaryLoading
  const anyThumbnails = tiles.some((t) => t.count > 0)

  return (
    <>
      {openTile ? (
        <FolderContents
          tile={openTile}
          onBack={() => setOpenTile(null)}
          onOpenJob={setSelectedJobId}
        />
      ) : gridLoading ? (
        <FolderGridSkeleton />
      ) : !anyThumbnails && folders.length === 0 ? (
        <p className="text-sm py-10 text-center" style={{ color: '#6b7280' }}>
          No thumbnails yet. Create one to generate your first asset.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {tiles.map((tile) => (
            <FolderCover key={tile.key} tile={tile} onOpen={setOpenTile} />
          ))}
        </div>
      )}

      {selectedJobId && (
        <ThumbnailDetailModal jobId={selectedJobId} onClose={() => setSelectedJobId(null)} />
      )}
    </>
  )
}
