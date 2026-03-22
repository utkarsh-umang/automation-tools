import { NavLink } from 'react-router-dom'
import logo from '@/assets/logo.png'
import { tools } from '@/config/tools'
import { ToolNavIcon } from '@/components/layout/ToolNavIcon'

function DashboardNavIcon() {
  const stroke = '#93c5fd'
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke={stroke} strokeWidth={1.8}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25v-2.25z"
      />
    </svg>
  )
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors',
    isActive ? 'font-semibold' : 'font-medium',
  ].join(' ')

const navLinkStyle = ({ isActive }: { isActive: boolean }) => ({
  borderLeft: '3px solid',
  borderLeftColor: isActive ? '#2563eb' : 'transparent',
  paddingLeft: isActive ? 7 : 10,
  color: isActive ? '#ffffff' : 'rgba(255,255,255,0.75)',
  backgroundColor: isActive ? 'rgba(37,99,235,0.15)' : 'transparent',
})

const iconWrapStyle = {
  background: 'rgba(37,99,235,0.3)',
  border: '1px solid rgba(37,99,235,0.5)',
} as const

export function Sidebar() {
  return (
    <aside
      className="flex h-full w-64 shrink-0 flex-col overflow-hidden border-r"
      style={{
        background: 'linear-gradient(180deg, #0a0f1e 0%, #0f1f4a 45%, #0a0f1e 100%)',
        borderColor: 'rgba(37,99,235,0.2)',
        boxShadow: 'inset -1px 0 0 rgba(37,99,235,0.12)',
      }}
    >
      <div className="shrink-0 border-b px-4 py-5" style={{ borderColor: 'rgba(37,99,235,0.2)' }}>
        <div className="flex items-center gap-3">
          <img src={logo} alt="" className="h-9 w-9 rounded-lg" />
          <div className="min-w-0">
            <p className="truncate text-sm font-bold leading-tight" style={{ color: '#ffffff' }}>
              Scale Brands Lab
            </p>
            <p className="text-[11px] font-medium uppercase tracking-wider" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Tools
            </p>
          </div>
        </div>
      </div>

      <nav className="flex min-h-0 flex-1 flex-col gap-0.5 overflow-hidden px-2 py-3">
        <NavLink to="/dashboard" end className={navLinkClass} style={navLinkStyle}>
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" style={iconWrapStyle}>
            <DashboardNavIcon />
          </span>
          <span className="min-w-0 flex-1 truncate">Dashboard</span>
        </NavLink>

        <div className="my-2 border-t px-1" style={{ borderColor: 'rgba(37,99,235,0.2)' }} aria-hidden />

        {tools.map((tool) => (
          <NavLink key={tool.id} to={tool.path} className={navLinkClass} style={navLinkStyle}>
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" style={iconWrapStyle}>
              <ToolNavIcon id={tool.iconId} />
            </span>
            <span className="min-w-0 flex-1 truncate">{tool.label}</span>
            <span
              className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
              style={
                tool.status === 'live'
                  ? {
                      background: 'rgba(34,197,94,0.2)',
                      border: '1px solid rgba(34,197,94,0.45)',
                      color: '#86efac',
                    }
                  : {
                      background: 'rgba(255,255,255,0.06)',
                      border: '1px solid rgba(255,255,255,0.12)',
                      color: 'rgba(255,255,255,0.45)',
                    }
              }
            >
              {tool.status === 'live' ? 'Live' : 'Soon'}
            </span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
