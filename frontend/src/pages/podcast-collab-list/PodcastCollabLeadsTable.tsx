import type { PodcastCollabRow } from './mockData'

export function PodcastCollabLeadsTable({ rows }: { rows: PodcastCollabRow[] }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border" style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff' }}>
      <div
        className="grid grid-cols-12 gap-2 border-b px-4 py-2 text-[11px] font-semibold uppercase tracking-wide"
        style={{
          borderColor: 'rgba(37,99,235,0.2)',
          color: 'rgba(255,255,255,0.65)',
          background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 60%, #0a0f1e 100%)',
        }}
      >
        <div className="col-span-3">Podcast</div>
        <div className="col-span-2">Host</div>
        <div className="col-span-2">Relevance</div>
        <div className="col-span-3">Podcast URL</div>
        <div className="col-span-2">Notes</div>
      </div>
      <div className="divide-y" style={{ borderColor: '#f3f4f6' }}>
        {rows.map((row) => (
          <div key={row.id} className="grid min-h-8 grid-cols-12 gap-2 px-4 py-1.5 text-sm items-center">
            <div className="col-span-3 truncate font-medium" style={{ color: '#111827' }} title={row.podcastName}>
              {row.podcastName}
            </div>
            <div className="col-span-2 truncate" style={{ color: '#6b7280' }} title={row.host}>
              {row.host}
            </div>
            <div className="col-span-2 tabular-nums" style={{ color: '#6b7280' }}>
              {row.relevancePct}%
            </div>
            <div className="col-span-3 truncate">
              <a
                href={row.podcastUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
                style={{ color: '#2563eb' }}
                title={row.podcastUrl}
              >
                {row.podcastUrl}
              </a>
            </div>
            <div className="col-span-2 truncate text-xs" style={{ color: '#6b7280' }} title={row.notes}>
              {row.notes}
            </div>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between border-t px-4 py-2" style={{ borderColor: '#e5e7eb' }}>
        <span className="text-xs" style={{ color: '#6b7280' }}>
          Total {rows.length} podcast{rows.length === 1 ? '' : 's'}
        </span>
      </div>
    </div>
  )
}
