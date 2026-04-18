import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, Copy, ExternalLink, Loader2 } from 'lucide-react'
import {
  MOCK_CHANNEL_SNIPPET,
  MOCK_PODCAST_LISTS,
  MOCK_ROWS,
  MOCK_SHEET_URL,
  type MockPodcastList,
} from './mockData'
import { downloadPodcastCollabCsv } from './podcastCollabCsv'

const PIPELINE_STEPS = [
  'Fetch channel description',
  'Run prompt / LangChain check (ChatGPT)',
  'Podcast search (100 pages)',
  'Add matches to list',
  'Ready to export',
] as const

type Phase = 'idle' | 'running' | 'done'
type Tab = 'list' | 'create'

function looksLikeUrl(value: string): boolean {
  const t = value.trim()
  if (!t) return false
  try {
    const u = new URL(t.startsWith('http') ? t : `https://${t}`)
    return u.protocol === 'http:' || u.protocol === 'https:'
  } catch {
    return false
  }
}

const cardShell = {
  border: '1px solid #e5e7eb',
  backgroundColor: '#ffffff',
  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
} as const

const headerBarStyle = {
  background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 100%)',
  borderBottom: '1px solid rgba(37,99,235,0.2)',
} as const

function ListStatusBadge({ status }: { status: MockPodcastList['status'] }) {
  const map = {
    ready: { label: 'Ready', bg: '#f0fdf4', border: '#bbf7d0', color: '#15803d' },
  } as const
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

function PodcastListCard({ list }: { list: MockPodcastList }) {
  const navigate = useNavigate()
  const rowCount = list.rows.length

  return (
    <button
      type="button"
      onClick={() => navigate(`/podscan/${list.id}`)}
      className="w-full rounded-xl p-4 text-left transition-shadow"
      style={{
        ...cardShell,
        borderColor: '#e5e7eb',
        boxShadow: cardShell.boxShadow,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(37,99,235,0.1)'
        e.currentTarget.style.borderColor = 'rgba(37,99,235,0.25)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = cardShell.boxShadow
        e.currentTarget.style.borderColor = '#e5e7eb'
      }}
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold" style={{ color: '#0a0f1e' }}>
            {list.name}
          </p>
          <p className="mt-0.5 text-sm" style={{ color: '#6b7280' }}>
            Channel:{' '}
            <span className="truncate" style={{ color: '#111827' }}>
              {list.channelUrl}
            </span>
          </p>
          <p className="mt-1 text-xs" style={{ color: '#9ca3af' }}>
            Created {new Date(list.createdAt).toLocaleString()}
          </p>
        </div>
        <ListStatusBadge status={list.status} />
      </div>
      <div className="flex items-center justify-between gap-2 text-sm">
        <span style={{ color: '#6b7280' }}>
          {rowCount} podcast{rowCount === 1 ? '' : 's'} in list
        </span>
        <span className="font-semibold" style={{ color: '#1d4ed8' }}>
          View table →
        </span>
      </div>
    </button>
  )
}

export function PodcastCollabListCreator() {
  const [tab, setTab] = useState<Tab>('list')
  const [channelUrl, setChannelUrl] = useState('')
  const [phase, setPhase] = useState<Phase>('idle')
  const [activeStepIndex, setActiveStepIndex] = useState(-1)
  const [copyDone, setCopyDone] = useState(false)
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  const clearTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
  }, [])

  useEffect(() => () => clearTimers(), [clearTimers])

  const runPipeline = () => {
    if (!looksLikeUrl(channelUrl)) return
    clearTimers()
    setPhase('running')
    setActiveStepIndex(0)

    const staggerMs = 520
    PIPELINE_STEPS.forEach((_, i) => {
      const t = setTimeout(() => {
        setActiveStepIndex(i)
        if (i === PIPELINE_STEPS.length - 1) {
          const done = setTimeout(() => {
            setPhase('done')
          }, 400)
          timersRef.current.push(done)
        }
      }, i * staggerMs)
      timersRef.current.push(t)
    })
  }

  const handleCopySheet = async () => {
    try {
      await navigator.clipboard.writeText(MOCK_SHEET_URL)
      setCopyDone(true)
      const t = setTimeout(() => setCopyDone(false), 2000)
      timersRef.current.push(t)
    } catch {
      setCopyDone(false)
    }
  }

  const canSubmit = looksLikeUrl(channelUrl) && phase !== 'running'
  const showPipeline = phase === 'running' || phase === 'done'

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: '#0a0f1e' }}>
            Podcast Collab List Creator
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed" style={{ color: '#6b7280' }}>
            Turn a YouTube channel into a Podscan-style lead list for outreach. This preview uses mock data.
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
            + New list
          </button>
        )}
      </div>

      <div className="mb-6 border-b" style={{ borderColor: '#e5e7eb' }}>
        <div className="flex gap-6">
          {(
            [
              ['list', 'Your lists'],
              ['create', 'Create list'],
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
          {MOCK_PODCAST_LISTS.map((list) => (
            <PodcastListCard key={list.id} list={list} />
          ))}
        </div>
      )}

      {tab === 'create' && (
        <div className="space-y-6">
          <div className="overflow-hidden rounded-xl" style={cardShell}>
            <div className="px-5 py-4" style={headerBarStyle}>
              <h2 className="text-base font-semibold" style={{ color: '#ffffff' }}>
                Create list
              </h2>
              <p className="mt-1 text-xs" style={{ color: 'rgba(255,255,255,0.55)' }}>
                Paste a YouTube channel URL to run the collab discovery pipeline (mock)
              </p>
            </div>
            <div className="space-y-4 px-5 py-5">
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
                  YouTube channel URL
                </span>
                <input
                  type="url"
                  value={channelUrl}
                  onChange={(e) => setChannelUrl(e.target.value)}
                  placeholder="https://www.youtube.com/@YourChannel"
                  className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none ring-blue-500 focus:ring-2"
                  style={{ borderColor: '#e5e7eb', color: '#111827' }}
                  disabled={phase === 'running'}
                />
              </label>
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={runPipeline}
                  disabled={!canSubmit}
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                  style={{
                    background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                    boxShadow: '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)',
                  }}
                >
                  {phase === 'running' ? (
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                      Building…
                    </span>
                  ) : (
                    'Build collab list'
                  )}
                </button>
                {phase === 'idle' && channelUrl.trim() && !looksLikeUrl(channelUrl) && (
                  <span className="text-xs" style={{ color: '#b45309' }}>
                    Enter a valid http(s) URL
                  </span>
                )}
              </div>
            </div>
          </div>

          {showPipeline && (
            <div className="overflow-hidden rounded-xl" style={cardShell}>
              <div className="px-5 py-4" style={headerBarStyle}>
                <h2 className="text-base font-semibold" style={{ color: '#ffffff' }}>
                  Pipeline
                </h2>
              </div>
              <div className="px-5 py-5">
                <ol className="space-y-3">
                  {PIPELINE_STEPS.map((label, i) => {
                    const complete = phase === 'done' || (phase === 'running' && i < activeStepIndex)
                    const current = phase === 'running' && i === activeStepIndex
                    return (
                      <li key={label} className="flex items-start gap-3">
                        <span
                          className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                          style={{
                            background: complete
                              ? 'linear-gradient(135deg, #22c55e, #16a34a)'
                              : current
                                ? 'linear-gradient(135deg, #2563eb, #1d4ed8)'
                                : '#f3f4f6',
                            color: complete || current ? '#ffffff' : '#9ca3af',
                          }}
                        >
                          {complete ? (
                            <Check className="h-4 w-4" strokeWidth={2.5} />
                          ) : current ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            i + 1
                          )}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium" style={{ color: '#111827' }}>
                            {label}
                          </p>
                          {i === 0 && (current || complete) && (
                            <p className="mt-1 text-xs leading-relaxed" style={{ color: '#6b7280' }}>
                              {MOCK_CHANNEL_SNIPPET}
                            </p>
                          )}
                        </div>
                      </li>
                    )
                  })}
                </ol>
              </div>
            </div>
          )}

          {phase === 'done' && (
            <div className="overflow-hidden rounded-xl" style={cardShell}>
              <div className="px-5 py-4" style={headerBarStyle}>
                <h2 className="text-base font-semibold" style={{ color: '#ffffff' }}>
                  Google Sheet
                </h2>
              </div>
              <div className="px-5 py-5">
                <p className="mb-3 text-sm" style={{ color: '#6b7280' }}>
                  Your list is synced to this sheet (mock link). Open <span className="font-medium" style={{ color: '#111827' }}>Your lists</span> and
                  choose a list to open the full table view.
                </p>
                <div
                  className="mb-4 flex flex-col gap-3 rounded-lg border px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between"
                  style={{ borderColor: '#e5e7eb', backgroundColor: '#f9fafb' }}
                >
                  <code className="min-w-0 flex-1 break-all text-xs" style={{ color: '#111827' }}>
                    {MOCK_SHEET_URL}
                  </code>
                  <div className="flex shrink-0 flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handleCopySheet}
                      className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold"
                      style={{ borderColor: '#e5e7eb', color: '#374151', backgroundColor: '#ffffff' }}
                    >
                      <Copy className="h-3.5 w-3.5" aria-hidden />
                      {copyDone ? 'Copied' : 'Copy link'}
                    </button>
                    <a
                      href={MOCK_SHEET_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold text-white"
                      style={{ background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' }}
                    >
                      <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                      Open
                    </a>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => downloadPodcastCollabCsv(MOCK_ROWS, 'podcast_collab_list.csv')}
                    className="rounded-lg px-4 py-2 text-sm font-semibold text-white"
                    style={{
                      background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                      boxShadow: '0 1px 2px rgba(37,99,235,0.35)',
                    }}
                  >
                    Export CSV
                  </button>
                  <a
                    href={MOCK_SHEET_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center rounded-lg border px-4 py-2 text-sm font-semibold"
                    style={{ borderColor: '#e5e7eb', color: '#374151', backgroundColor: '#ffffff' }}
                  >
                    Open Google Sheet
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
