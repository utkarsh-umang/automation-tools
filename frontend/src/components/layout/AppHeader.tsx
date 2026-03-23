import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

interface AppHeaderProps {
  /** Breadcrumb segment after the brand (e.g. "Dashboard", "YouTube Script"). */
  breadcrumb?: string
}

export function AppHeader({ breadcrumb }: AppHeaderProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header
      style={{
        background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 60%, #0a0f1e 100%)',
        borderBottom: '1px solid rgba(37,99,235,0.2)',
        boxShadow: '0 1px 0 rgba(37,99,235,0.15), 0 4px 20px rgba(0,0,0,0.4)',
      }}
    >
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <span
            className="hidden truncate text-xm sm:block"
            style={{ color: 'rgba(255,255,255,0.65)' }}
          >
            {breadcrumb ?? 'Tools'}
          </span>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          {user && (
            <div className="flex items-center gap-2">
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
            type="button"
            onClick={handleLogout}
            className="rounded-lg px-3 py-1.5 text-sm font-medium transition-all"
            style={{
              border: '1px solid rgba(255,255,255,0.15)',
              color: 'rgba(255,255,255,0.7)',
              backgroundColor: 'rgba(255,255,255,0.05)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)'
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)'
              e.currentTarget.style.color = '#ffffff'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)'
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)'
              e.currentTarget.style.color = 'rgba(255,255,255,0.7)'
            }}
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  )
}
