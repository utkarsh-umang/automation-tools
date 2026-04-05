import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { ScrollToTop } from '@/components/ScrollToTop'
import { ComingSoonScreen } from '@/pages/ComingSoonScreen'
import { Dashboard } from '@/pages/Dashboard'
import { Login } from '@/pages/Login'
import { BatchDetailPage } from '@/pages/youtube-script/BatchDetailPage'
import { YouTubeScriptLayout } from '@/pages/youtube-script/YouTubeScriptLayout'
import { YouTubeScriptTool } from '@/pages/youtube-script/YouTubeScriptTool'
import { ThumbnailProject } from '@/pages/thumbnail-project'

function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />

          <Route path="/youtube-script" element={<YouTubeScriptLayout />}>
            <Route index element={<YouTubeScriptTool />} />
            <Route path="batch/:batchId" element={<BatchDetailPage />} />
          </Route>

          <Route
            path="/library-lp"
            element={
              <AppShell breadcrumb="Library LP Creator">
                <ComingSoonScreen
                  title="Library LP Creator"
                  description="Generate landing pages from your content library templates."
                />
              </AppShell>
            }
          />
          <Route
            path="/podscan"
            element={
              <AppShell breadcrumb="Podscan List">
                <ComingSoonScreen
                  title="Podscan List Builder"
                  description="Build podcast lead lists from targeted scans."
                />
              </AppShell>
            }
          />
          <Route
            path="/lead-magnet-pdf"
            element={
              <AppShell breadcrumb="Lead Magnet PDF">
                <ComingSoonScreen
                  title="Lead Magnet PDF"
                  description="Create client-ready PDF lead magnets from outlines."
                />
              </AppShell>
            }
          />
          <Route
            path="/thumbnail"
            element={
              <AppShell breadcrumb="Thumbnail Project">
                <ThumbnailProject />
              </AppShell>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  )
}

export { App }
