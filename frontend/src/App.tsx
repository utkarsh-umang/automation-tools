import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { AdminRoute } from '@/components/AdminRoute'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { ScrollToTop } from '@/components/ScrollToTop'
import { AdminUsers } from '@/pages/AdminUsers'
import { ComingSoonScreen } from '@/pages/ComingSoonScreen'
import { Dashboard } from '@/pages/Dashboard'
import { Login } from '@/pages/Login'
import { BatchDetailPage } from '@/pages/youtube-script/BatchDetailPage'
import { YouTubeScriptLayout } from '@/pages/youtube-script/YouTubeScriptLayout'
import { YouTubeScriptTool } from '@/pages/youtube-script/YouTubeScriptTool'
import { PodcastCollabListCreator, PodcastCollabListCreatorTableView } from '@/pages/podcast-collab-list'
import { ThumbnailProject } from '@/pages/thumbnail-project'
import { HooksAnalyzer } from '@/pages/HooksAnalyzer'

function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />

          <Route
            path="/thumbnail"
            element={
              <AppShell breadcrumb="Thumbnail Creator">
                <ThumbnailProject />
              </AppShell>
            }
          />

          {/* MEMBER accounts are restricted to the thumbnail creator above — everything
              below is ADMIN-only, mirroring the backend's require_roles("ADMIN") gating. */}
          <Route element={<AdminRoute />}>
            <Route
              path="/admin/users"
              element={
                <AppShell breadcrumb="Manage Users">
                  <AdminUsers />
                </AppShell>
              }
            />

            <Route path="/youtube-script" element={<YouTubeScriptLayout />}>
              <Route index element={<YouTubeScriptTool />} />
              <Route path="batch/:batchId" element={<BatchDetailPage />} />
            </Route>

            <Route path="/hooks-analyzer" element={<AppShell><HooksAnalyzer /></AppShell>} />

            <Route
              path="/podscan"
              element={
                <AppShell breadcrumb="Podcast Collab List Creator">
                  <PodcastCollabListCreator />
                </AppShell>
              }
            />
            <Route
              path="/podscan/:id"
              element={<PodcastCollabListCreatorTableView />}
            />

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
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  )
}

export { App }
