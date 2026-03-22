import { Outlet } from 'react-router-dom'
import { YouTubeScriptProvider } from '@/context/YouTubeScriptProvider'

export function YouTubeScriptLayout() {
  return (
    <YouTubeScriptProvider>
      <Outlet />
    </YouTubeScriptProvider>
  )
}
