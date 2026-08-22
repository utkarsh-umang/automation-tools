/**
 * Global handling for a session that expired while the app was open.
 *
 * Access tokens last 24h and there is no refresh token, so a tab left open
 * overnight wakes up holding a dead token. `AuthContext` only checks expiry on
 * mount, and `ProtectedRoute` only reads `isAuthenticated` from React state, so
 * nothing in the app notices: the shell keeps rendering as logged-in and every
 * panel fails with an error banner. That reads as "the backend is down" — it is
 * what two users hit on 2026-08-21 and 2026-08-22, clicking around a dead
 * session for tens of minutes before manually logging in again.
 *
 * The fix is to treat a 401 from the server as the authoritative signal that the
 * session is over, wherever it happens, and drive the same logout the app
 * already performs on mount.
 */

import type { AxiosError, AxiosInstance } from 'axios'

const SESSION_EXPIRED_EVENT = 'auth:session-expired'

/** URLs where a 401 means "wrong credentials", not "your session ended". */
const LOGIN_PATH = '/api/v1/auth/login'

export function notifySessionExpired(): void {
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
}

/** Subscribe to session expiry. Returns an unsubscribe function. */
export function onSessionExpired(handler: () => void): () => void {
  window.addEventListener(SESSION_EXPIRED_EVENT, handler)
  return () => window.removeEventListener(SESSION_EXPIRED_EVENT, handler)
}

/**
 * True if this failure should end the session.
 *
 * A 401 from the login endpoint is a rejected password and must be left alone —
 * bouncing it through logout would wipe the error message the login form is
 * about to show. Anonymous 401s (no token held) are ignored too, so a stray
 * failure on the login screen cannot start a redirect loop.
 */
export function isSessionExpiryError(status: number, url: string | undefined, hasToken: boolean): boolean {
  if (status !== 401 || !hasToken) return false
  return !(url ?? '').includes(LOGIN_PATH)
}

/**
 * Register the 401 → logout bridge on the axios instance the generated client
 * uses (`request.ts` defaults to the global `axios`).
 *
 * The interceptor observes and re-throws: `sendRequest` catches the rejection
 * and hands the response back to `catchErrorCodes`, so callers still receive the
 * `ApiError` they already handle and per-page error states are unchanged.
 */
export function installSessionExpiryInterceptor(axiosInstance: AxiosInstance, hasToken: () => boolean): number {
  return axiosInstance.interceptors.response.use(
    (response) => response,
    (error: unknown) => {
      const response = (error as AxiosError | undefined)?.response
      const config = (error as AxiosError | undefined)?.config
      if (response && isSessionExpiryError(response.status, config?.url, hasToken())) {
        notifySessionExpired()
      }
      return Promise.reject(error)
    },
  )
}
