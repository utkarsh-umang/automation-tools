import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

export function ProtectedRoute() {
  const { isAuthenticated, isInitialized } = useAuth()

  // Wait for localStorage restore to complete before evaluating auth state.
  // Without this, a page refresh redirects to /login before the token is read.
  if (!isInitialized) {
    return null
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
