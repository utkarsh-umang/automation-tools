import { useState } from 'react'
import { isValidSearchTermsFormat, parseQuotedTerms } from '@/utils/searchTerms'

interface CreateBatchFormProps {
  onCancel: () => void
  onCreated: () => void
  onSubmitBatch: (payload: { name: string; keyword: string; searchTerms: string[] }) => void
}

export function CreateBatchForm({ onCancel, onCreated, onSubmitBatch }: CreateBatchFormProps) {
  const [name, setName] = useState('')
  const [keyword, setKeyword] = useState('')
  const [termsRaw, setTermsRaw] = useState('')

  const trimmedName = name.trim()
  const trimmedKeyword = keyword.trim()
  const formatOk = termsRaw.length === 0 ? false : isValidSearchTermsFormat(termsRaw)
  const parsedTerms = formatOk ? parseQuotedTerms(termsRaw) : []
  const termsError =
    termsRaw.length > 0 && !formatOk
      ? 'Some terms are not formatted correctly — make sure every term is wrapped in double quotes and separated by commas.'
      : null

  const submitDisabled =
    trimmedName.length === 0 ||
    trimmedKeyword.length === 0 ||
    !formatOk ||
    parsedTerms.length === 0 ||
    Boolean(termsError)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const nErr = trimmedName.length === 0 ? 'Batch name is required.' : null
    const kErr = trimmedKeyword.length === 0 ? 'Keyword is required.' : null
    const tErr = termsRaw.trim().length === 0 ? 'Search terms are required.' : null
    if (nErr || kErr || tErr || !formatOk) return

    onSubmitBatch({
      name: trimmedName,
      keyword: trimmedKeyword,
      searchTerms: parseQuotedTerms(termsRaw),
    })
    onCreated()
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl"
      style={{
        border: '1px solid #e5e7eb',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}
    >
      <div
        className="px-5 py-4"
        style={{
          background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 100%)',
          borderBottom: '1px solid rgba(37,99,235,0.2)',
        }}
      >
        <h2 className="text-base font-semibold" style={{ color: '#ffffff' }}>
          Create batch
        </h2>
        <p className="mt-1 text-xs" style={{ color: 'rgba(255,255,255,0.55)' }}>
          Define a name, category label, and quoted search terms
        </p>
      </div>

      <div className="space-y-5 px-5 py-5">
        <div
          className="rounded-lg border px-3 py-2.5 text-sm"
          style={{
            backgroundColor: '#eff6ff',
            borderColor: 'rgba(37,99,235,0.25)',
            color: '#1e3a8a',
          }}
        >
          YouTube Data API quota is <strong>10,000 credits per day</strong> (~100 terms). Batches with more
          than ~100 terms will continue across multiple days automatically.
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
            Batch name <span style={{ color: '#be123c' }}>*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
            style={{
              border: `1px solid ${name && trimmedName.length === 0 ? '#fecdd3' : '#e5e7eb'}`,
              color: '#111827',
              backgroundColor: '#f9fafb',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = '#2563eb'
              e.target.style.backgroundColor = '#ffffff'
              e.target.style.boxShadow = '0 0 0 3px rgba(37,99,235,0.12)'
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#e5e7eb'
              e.target.style.backgroundColor = '#f9fafb'
              e.target.style.boxShadow = 'none'
            }}
            placeholder="e.g. Q1 podcast outreach"
          />
          {name && trimmedName.length === 0 && (
            <p className="mt-1 text-xs" style={{ color: '#be123c' }}>
              Batch name is required.
            </p>
          )}
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
            Keyword / category <span style={{ color: '#be123c' }}>*</span>
          </label>
          <p className="mb-1.5 text-xs" style={{ color: '#6b7280' }}>
            This is a label for your batch only — it is not sent as a search filter to YouTube.
          </p>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
            style={{
              border: `1px solid ${keyword && trimmedKeyword.length === 0 ? '#fecdd3' : '#e5e7eb'}`,
              color: '#111827',
              backgroundColor: '#f9fafb',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = '#2563eb'
              e.target.style.backgroundColor = '#ffffff'
              e.target.style.boxShadow = '0 0 0 3px rgba(37,99,235,0.12)'
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#e5e7eb'
              e.target.style.backgroundColor = '#f9fafb'
              e.target.style.boxShadow = 'none'
            }}
            placeholder="e.g. Podcasts"
          />
          {keyword && trimmedKeyword.length === 0 && (
            <p className="mt-1 text-xs" style={{ color: '#be123c' }}>
              Keyword is required.
            </p>
          )}
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
            Search terms <span style={{ color: '#be123c' }}>*</span>
          </label>
          <p className="mb-1.5 text-xs" style={{ color: '#6b7280' }}>
            Format: each term in double quotes, separated by commas —{' '}
            <code className="rounded bg-gray-100 px-1 py-0.5 text-[11px]" style={{ color: '#374151' }}>
              &quot;term one&quot;, &quot;term two&quot;
            </code>
          </p>
          <textarea
            value={termsRaw}
            onChange={(e) => setTermsRaw(e.target.value)}
            rows={5}
            className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
            style={{
              border: `1px solid ${termsError ? '#fecdd3' : '#e5e7eb'}`,
              color: '#111827',
              backgroundColor: '#f9fafb',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = '#2563eb'
              e.target.style.backgroundColor = '#ffffff'
              e.target.style.boxShadow = '0 0 0 3px rgba(37,99,235,0.12)'
            }}
            onBlur={(e) => {
              e.target.style.borderColor = termsError ? '#fecdd3' : '#e5e7eb'
              e.target.style.backgroundColor = '#f9fafb'
              e.target.style.boxShadow = 'none'
            }}
            placeholder={`"podcast host", "content creator", "youtube creator coaching"`}
          />
          {termsError && (
            <p className="mt-1 text-xs" style={{ color: '#be123c' }}>
              {termsError}
            </p>
          )}
        </div>

        <div>
          <p className="mb-2 text-sm font-medium" style={{ color: '#111827' }}>
            Preview — {parsedTerms.length} terms
          </p>
          {termsRaw.length === 0 ? (
            <p className="text-sm" style={{ color: '#9ca3af' }}>
              Parsed terms will appear here…
            </p>
          ) : termsError ? (
            <p className="text-sm" style={{ color: '#be123c' }}>
              Fix formatting above to see preview
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {parsedTerms.map((t, i) => (
                <span
                  key={`${i}-${t}`}
                  className="rounded-full px-2.5 py-1 text-xs font-medium"
                  style={{
                    backgroundColor: '#eff6ff',
                    border: '1px solid rgba(37,99,235,0.25)',
                    color: '#1e40af',
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div
        className="flex flex-wrap items-center justify-end gap-3 border-t px-5 py-4"
        style={{ borderColor: '#e5e7eb' }}
      >
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg px-4 py-2 text-sm font-medium"
          style={{
            border: '1px solid #e5e7eb',
            color: '#374151',
            backgroundColor: '#ffffff',
          }}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitDisabled}
          className="rounded-lg px-4 py-2 text-sm font-semibold text-white transition-all disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
            boxShadow: '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)',
          }}
        >
          Create Batch
        </button>
      </div>
    </form>
  )
}
