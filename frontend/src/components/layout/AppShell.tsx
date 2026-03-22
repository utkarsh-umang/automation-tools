import type { ReactNode } from 'react'
import { AppHeader } from '@/components/layout/AppHeader'
import { Sidebar } from '@/components/layout/Sidebar'

interface AppShellProps {
  children: ReactNode
  breadcrumb?: string
}

export function AppShell({ children, breadcrumb }: AppShellProps) {
  return (
    <div
      className="flex h-svh max-h-svh w-full flex-col overflow-hidden"
      style={{ backgroundColor: '#0a0f1e' }}
    >
      <div className="flex min-h-0 w-full flex-1">
        <Sidebar />
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <div className="shrink-0">
            <AppHeader breadcrumb={breadcrumb} />
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto" style={{ backgroundColor: '#f9fafb' }}>
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
