import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import axios from 'axios'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { OpenAPI } from '@/client'
import { apiBaseUrl } from '@/config/api'
import { getToken } from '@/utils/token'
import { installSessionExpiryInterceptor } from '@/utils/sessionExpiry'
import { App } from './App'
import { ErrorBoundary } from './components/ErrorBoundary'
import { AuthProvider } from './context/AuthContext'
import './index.css'

OpenAPI.BASE = apiBaseUrl

// A 401 anywhere means the 24h token died while the tab was open. Without this
// the app keeps rendering a logged-in shell whose every request fails.
installSessionExpiryInterceptor(axios, () => getToken() !== null)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <BrowserRouter>
          <AuthProvider>
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
              <App />
            </div>
          </AuthProvider>
        </BrowserRouter>
      </ErrorBoundary>
    </QueryClientProvider>
  </StrictMode>,
)
