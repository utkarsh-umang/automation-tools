/**
 * API base URL for the generated client.
 *
 * In development: Vite proxies /api and /health to http://127.0.0.1:8000
 * (see vite.config.ts), so relative paths work with no extra config.
 *
 * In production: nginx serves the React build and proxies /api and /health
 * to the backend container (see frontend/nginx.conf), so relative paths
 * also work out of the box.
 *
 * Override with VITE_API_BASE_URL only when the API is on a different domain
 * (e.g. VITE_API_BASE_URL=https://api.example.com).
 */
const raw = import.meta.env.VITE_API_BASE_URL
const apiBaseUrl =
  typeof raw === 'string' && raw.trim() !== '' ? raw.trim() : ''

export { apiBaseUrl }
