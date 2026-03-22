interface ComingSoonScreenProps {
  title: string
  description: string
}

export function ComingSoonScreen({ title, description }: ComingSoonScreenProps) {
  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <div
        className="overflow-hidden rounded-xl"
        style={{
          border: '1px solid #e5e7eb',
          backgroundColor: '#ffffff',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <div
          className="px-6 py-4"
          style={{
            background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 100%)',
            borderBottom: '1px solid rgba(37,99,235,0.2)',
          }}
        >
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-lg font-semibold" style={{ color: '#ffffff' }}>
              {title}
            </h1>
            <span
              className="rounded px-2 py-0.5 text-xs font-semibold"
              style={{
                background: 'rgba(37,99,235,0.25)',
                border: '1px solid rgba(37,99,235,0.5)',
                color: '#93c5fd',
              }}
            >
              Planned
            </span>
          </div>
        </div>
        <div className="px-6 py-8">
          <p className="text-sm leading-relaxed" style={{ color: '#6b7280' }}>
            {description}
          </p>
          <p className="mt-6 text-sm font-medium" style={{ color: '#111827' }}>
            This tool is on the roadmap. Navigation is wired so the team can preview the full workspace.
          </p>
        </div>
      </div>
    </main>
  )
}
