interface ToolCardProps {
  title: string
  description: string
  tags: string[]
  status: 'live' | 'planned'
  featured?: boolean
  onClick: () => void
  children?: React.ReactNode
}

export function ToolCard({
  title,
  description,
  tags,
  status,
  featured,
  onClick,
  children,
}: ToolCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-xl text-left transition-shadow"
      style={{
        border: '1px solid #e5e7eb',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(37,99,235,0.12)'
        e.currentTarget.style.borderColor = 'rgba(37,99,235,0.35)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)'
        e.currentTarget.style.borderColor = '#e5e7eb'
      }}
    >
      {featured ? (
        <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-stretch sm:gap-6">
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-semibold" style={{ color: '#0a0f1e' }}>
                {title}
              </h3>
              <span
                className="rounded px-2 py-0.5 text-xs font-semibold"
                style={{
                  background: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  color: '#15803d',
                }}
              >
                Live
              </span>
            </div>
            <p className="text-sm leading-relaxed" style={{ color: '#6b7280' }}>
              {description}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {tags.map((t) => (
                <span
                  key={t}
                  className="rounded-full px-2.5 py-0.5 text-xs font-medium"
                  style={{ backgroundColor: '#f3f4f6', color: '#374151' }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
          {children}
        </div>
      ) : (
        <div className="p-5">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold" style={{ color: '#0a0f1e' }}>
              {title}
            </h3>
            <span
              className="rounded px-2 py-0.5 text-xs font-semibold"
              style={
                status === 'live'
                  ? {
                      background: '#f0fdf4',
                      border: '1px solid #bbf7d0',
                      color: '#15803d',
                    }
                  : {
                      background: '#f9fafb',
                      border: '1px solid #e5e7eb',
                      color: '#6b7280',
                    }
              }
            >
              {status === 'live' ? 'Live' : 'Planned'}
            </span>
          </div>
          <p className="text-sm leading-relaxed" style={{ color: '#6b7280' }}>
            {description}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {tags.map((t) => (
              <span
                key={t}
                className="rounded-full px-2.5 py-0.5 text-xs font-medium"
                style={{ backgroundColor: '#f3f4f6', color: '#374151' }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </button>
  )
}
