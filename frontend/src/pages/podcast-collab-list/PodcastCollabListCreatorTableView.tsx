import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Copy, ExternalLink } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { getMockPodcastListById } from './mockData'
import { PodcastCollabLeadsTable } from './PodcastCollabLeadsTable'
import { downloadPodcastCollabCsv } from './podcastCollabCsv'

export function PodcastCollabListCreatorTableView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const list = id ? getMockPodcastListById(id) : undefined
  const [copyDone, setCopyDone] = useState(false)

  function goBack() {
    navigate('/podscan')
  }

  async function handleCopySheet(url: string) {
    try {
      await navigator.clipboard.writeText(url)
      setCopyDone(true)
      window.setTimeout(() => setCopyDone(false), 2000)
    } catch {
      setCopyDone(false)
    }
  }

  if (!id || !list) {
    return (
      <AppShell breadcrumb="Podcast Collab List Creator">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <p className="text-sm" style={{ color: '#6b7280' }}>
            List not found.
          </p>
          <button type="button" onClick={goBack} className="mt-4 text-sm font-medium" style={{ color: '#2563eb' }}>
            ← Back to your lists
          </button>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell breadcrumb="Podcast Collab List Creator">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div
          className="mb-6 flex flex-col gap-3 rounded-xl border px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
          style={{ borderColor: '#e5e7eb', backgroundColor: '#ffffff', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}
        >
          <div className="min-w-0">
            <button
              type="button"
              onClick={goBack}
              className="mb-1 inline-flex items-center gap-1 text-xs font-medium"
              style={{ color: '#2563eb' }}
            >
              ← Back to your lists
            </button>
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
              List detail
            </p>
            <h1 className="truncate text-lg font-semibold" style={{ color: '#0a0f1e' }}>
              {list.name}
            </h1>
            <p className="mt-0.5 truncate text-xs" style={{ color: '#6b7280' }}>
              {list.channelUrl}
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => handleCopySheet(list.sheetUrl)}
              className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold"
              style={{ borderColor: '#e5e7eb', color: '#374151', backgroundColor: '#ffffff' }}
            >
              <Copy className="h-3.5 w-3.5" aria-hidden />
              {copyDone ? 'Copied' : 'Copy sheet link'}
            </button>
            <a
              href={list.sheetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold text-white"
              style={{ background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' }}
            >
              <ExternalLink className="h-3.5 w-3.5" aria-hidden />
              Open Google Sheet
            </a>
            <button
              type="button"
              onClick={() => downloadPodcastCollabCsv(list.rows, `podcast_collab_${list.id}.csv`)}
              className="rounded-lg px-3 py-1.5 text-xs font-semibold text-white"
              style={{
                background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                boxShadow: '0 1px 2px rgba(37,99,235,0.35)',
              }}
            >
              Export CSV
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <PodcastCollabLeadsTable rows={list.rows} />
        </div>
      </div>
    </AppShell>
  )
}
