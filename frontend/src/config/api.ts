/**
 * API base URL for the generated client. Same in dev and prod.
 * Set VITE_API_BASE_URL in frontend/.env (e.g. http://127.0.0.1:8000).
 * Backend must allow this origin in CORS_ORIGINS (e.g. http://localhost:5173).
 */
const raw = import.meta.env.VITE_API_BASE_URL
const apiBaseUrl =
  (typeof raw === 'string' && raw.trim() !== '' ? raw.trim() : null) ??
  'http://127.0.0.1:8000'

export { apiBaseUrl }
