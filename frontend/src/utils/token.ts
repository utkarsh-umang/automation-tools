const TOKEN_KEY = 'auth_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

/** Decode the payload of a JWT without verifying the signature. */
export function decodeTokenPayload(token: string): Record<string, unknown> | null {
  try {
    const base64 = token.split('.')[1]
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json) as Record<string, unknown>
  } catch {
    return null
  }
}

/**
 * True if the token is missing, malformed, or past its `exp` claim. Used so an
 * expired token isn't treated as a live session (the backend rejects it with
 * 401 anyway, but this avoids showing a logged-in shell that can't load data).
 */
export function isTokenExpired(token: string | null): boolean {
  if (!token) return true
  const exp = decodeTokenPayload(token)?.exp
  if (typeof exp !== 'number') return true
  return Date.now() >= exp * 1000
}
