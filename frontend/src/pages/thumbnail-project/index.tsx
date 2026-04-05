import { useState } from 'react'
import { YourThumbnails } from './YourThumbnails'
import { CreateThumbnail } from './CreateThumbnail'

type Tab = 'list' | 'create'

export function ThumbnailProject() {
  const [tab, setTab] = useState<Tab>('list')

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: '#0a0f1e' }}>
            Thumbnail Project
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed" style={{ color: '#6b7280' }}>
            Manage and curate your visual assets for high-impact editorial storytelling.
            Generate thumbnails with AI.
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
            + New Thumbnail
          </button>
        )}
      </div>

      <div className="mb-6 border-b" style={{ borderColor: '#e5e7eb' }}>
        <div className="flex gap-6">
          {(
            [
              ['list', 'Your Thumbnails'],
              ['create', 'Create Thumbnail'],
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

      <div className="space-y-4">
        {tab === 'list' ? <YourThumbnails /> : <CreateThumbnail />}
      </div>
    </div>
  )
}
