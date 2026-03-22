import type { ReactNode } from 'react'
import { AppHeader } from '@/components/layout/AppHeader'
import { Sidebar } from '@/components/layout/Sidebar'

interface AppShellProps {
  children: ReactNode
  breadcrumb?: string
}

export function AppShell({ children, breadcrumb }: AppShellProps) {
  return (
    <div className="flex min-h-svh w-full flex-col" style={{ backgroundColor: '#0a0f1e' }}>
      <div className="flex min-h-svh w-full flex-1">
        <Sidebar />
        <div className="flex min-h-svh min-w-0 flex-1 flex-col">
          <AppHeader breadcrumb={breadcrumb} />
          <div className="min-h-0 flex-1 overflow-auto" style={{ backgroundColor: '#f9fafb' }}>
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
