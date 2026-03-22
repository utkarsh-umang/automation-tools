import { NavLink } from 'react-router-dom'
import logo from '@/assets/logo.png'
import { tools } from '@/config/tools'
import { ToolNavIcon } from '@/components/layout/ToolNavIcon'

export function Sidebar() {
  return (
    <aside
      className="flex h-full w-64 shrink-0 flex-col border-r"
      style={{
        background: 'linear-gradient(180deg, #0a0f1e 0%, #0f1f4a 45%, #0a0f1e 100%)',
        borderColor: 'rgba(37,99,235,0.2)',
        boxShadow: 'inset -1px 0 0 rgba(37,99,235,0.12)',
      }}
    >
      <div className="border-b px-4 py-5" style={{ borderColor: 'rgba(37,99,235,0.2)' }}>
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

      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-2 py-3">
        {tools.map((tool) => (
          <NavLink
            key={tool.id}
            to={tool.path}
            className={({ isActive }) =>
              [
                'group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors',
                isActive ? 'font-semibold' : 'font-medium',
              ].join(' ')
            }
            style={({ isActive }) => ({
              borderLeft: '3px solid',
              borderLeftColor: isActive ? '#2563eb' : 'transparent',
              paddingLeft: isActive ? 7 : 10,
              color: isActive ? '#ffffff' : 'rgba(255,255,255,0.75)',
              backgroundColor: isActive ? 'rgba(37,99,235,0.15)' : 'transparent',
            })}
          >
            <span
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
              style={{
                background: 'rgba(37,99,235,0.3)',
                border: '1px solid rgba(37,99,235,0.5)',
              }}
            >
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
