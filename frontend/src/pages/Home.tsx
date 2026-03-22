import { useNavigate } from 'react-router-dom'
import logo from '@/assets/logo.png'
import { useHealthQuery } from '@/hooks/api/useHealthQuery'
import { useAuth } from '@/hooks/useAuth'
import { Loader } from '@/components/Loader'

export function Home() {
  const { data, isLoading, error } = useHealthQuery()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div style={{ backgroundColor: '#f9fafb', minHeight: '100vh' }}>
      {/* ── Header ── */}
      <header
        style={{
          background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 60%, #0a0f1e 100%)',
          borderBottom: '1px solid rgba(37,99,235,0.2)',
          boxShadow: '0 1px 0 rgba(37,99,235,0.15), 0 4px 20px rgba(0,0,0,0.4)',
        }}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <img src={logo} alt="Logo" className="h-9 w-9 rounded-lg" />
            <span className="text-sm font-semibold" style={{ color: '#ffffff' }}>
              Automation Tools
            </span>
            {/* Blue accent line */}
            <div
              className="hidden h-4 w-px sm:block"
              style={{ backgroundColor: 'rgba(37,99,235,0.4)' }}
            />
            <span
              className="hidden text-xs sm:block"
              style={{ color: 'rgba(255,255,255,0.35)' }}
            >
              Dashboard
            </span>
          </div>

          {/* User + sign out */}
          <div className="flex items-center gap-3">
            {user && (
              <div className="flex items-center gap-2">
                {/* Avatar placeholder */}
                <div
                  className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold"
                  style={{
                    background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
                    color: '#ffffff',
                  }}
                >
                  {user.email.charAt(0).toUpperCase()}
                </div>
                <span className="hidden text-sm sm:block" style={{ color: 'rgba(255,255,255,0.65)' }}>
                  {user.email}
                </span>
                <span
                  className="rounded px-1.5 py-0.5 text-xs font-semibold"
                  style={{
                    background: 'rgba(37,99,235,0.25)',
                    border: '1px solid rgba(37,99,235,0.5)',
                    color: '#93c5fd',
                  }}
                >
                  {user.role}
                </span>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="rounded-lg px-3 py-1.5 text-sm font-medium transition-all"
              style={{
                border: '1px solid rgba(255,255,255,0.15)',
                color: 'rgba(255,255,255,0.7)',
                backgroundColor: 'rgba(255,255,255,0.05)',
              }}
              onMouseEnter={(e) => {
                ;(e.currentTarget).style.backgroundColor = 'rgba(255,255,255,0.1)'
                ;(e.currentTarget).style.borderColor = 'rgba(255,255,255,0.25)'
                ;(e.currentTarget).style.color = '#ffffff'
              }}
              onMouseLeave={(e) => {
                ;(e.currentTarget).style.backgroundColor = 'rgba(255,255,255,0.05)'
                ;(e.currentTarget).style.borderColor = 'rgba(255,255,255,0.15)'
                ;(e.currentTarget).style.color = 'rgba(255,255,255,0.7)'
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* ── Content ── */}
      <main className="mx-auto max-w-7xl px-6 py-10">
        {/* Page title */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold" style={{ color: '#0a0f1e' }}>
            Dashboard
          </h1>
          <p className="mt-1 text-sm" style={{ color: '#6b7280' }}>
            Overview of your system status
          </p>
        </div>

        {/* Health card */}
        <div
          className="overflow-hidden rounded-xl"
          style={{
            border: '1px solid #e5e7eb',
            backgroundColor: '#ffffff',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          {/* Card header */}
          <div
            className="flex items-center gap-3 px-5 py-4"
            style={{
              background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 100%)',
              borderBottom: '1px solid rgba(37,99,235,0.2)',
            }}
          >
            <div
              className="flex h-8 w-8 items-center justify-center rounded-lg"
              style={{ background: 'rgba(37,99,235,0.3)', border: '1px solid rgba(37,99,235,0.5)' }}
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="#93c5fd"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <span className="text-sm font-semibold" style={{ color: '#ffffff' }}>
              System Health
            </span>
          </div>

          {/* Card body */}
          <div className="px-5 py-5">
            {isLoading && (
              <div className="flex items-center gap-2 text-sm" style={{ color: '#6b7280' }}>
                <Loader />
                <span>Checking services…</span>
              </div>
            )}
            {error && (
              <div
                className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm"
                style={{
                  backgroundColor: '#fff1f2',
                  border: '1px solid #fecdd3',
                  color: '#be123c',
                }}
              >
                <svg className="h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                API unreachable: {error instanceof Error ? error.message : 'Unknown error'}
              </div>
            )}
            {data && (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {[
                  { label: 'Postgres', value: data.postgres },
                  { label: 'MongoDB', value: data.mongo },
                  { label: 'Redis', value: data.redis },
                ].map((svc) => {
                  const ok = svc.value?.toLowerCase() === 'ok' || svc.value?.toLowerCase() === 'connected'
                  return (
                    <div
                      key={svc.label}
                      className="flex items-center justify-between rounded-lg px-4 py-3"
                      style={{
                        border: `1px solid ${ok ? '#bbf7d0' : '#fecdd3'}`,
                        backgroundColor: ok ? '#f0fdf4' : '#fff1f2',
                      }}
                    >
                      <div>
                        <p className="text-xs font-medium" style={{ color: '#6b7280' }}>
                          {svc.label}
                        </p>
                        <p
                          className="mt-0.5 text-sm font-semibold capitalize"
                          style={{ color: ok ? '#15803d' : '#be123c' }}
                        >
                          {svc.value ?? '—'}
                        </p>
                      </div>
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: ok ? '#22c55e' : '#f43f5e' }}
                      />
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Status overview row */}
        {data && (
          <div className="mt-4 flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: '#22c55e' }} />
            <p className="text-xs" style={{ color: '#6b7280' }}>
              All services operational · Status:{' '}
              <span className="font-medium" style={{ color: '#0a0f1e' }}>
                {data.status}
              </span>
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
