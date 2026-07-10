import { createContext, useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { OpenAPI, UsersService } from '@/client'
import type { AuthUser } from '@/types/auth'
import { getToken, isTokenExpired, removeToken, setToken } from '@/utils/token'

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  isInitialized: boolean
  login: (token: string, user?: AuthUser) => void
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setTokenState] = useState<string | null>(null)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)

  // Restore session from localStorage on mount — must complete before
  // ProtectedRoute evaluates isAuthenticated, otherwise a refresh causes
  // an immediate redirect to /login before the token is read.
  useEffect(() => {
    const stored = getToken()
    if (stored && !isTokenExpired(stored)) {
      OpenAPI.TOKEN = stored
      setTokenState(stored)
      try {
        const storedUser = localStorage.getItem('auth_user')
        if (storedUser) {
          setUser(JSON.parse(storedUser) as AuthUser)
        }
      } catch {
        // ignore parse errors
      }
      setIsInitialized(true)
      // Re-fetch the profile so role changes (e.g. an admin promoting a
      // member) take effect without forcing a logout/login cycle.
      UsersService.getMeApiV1UsersMeGet()
        .then((me) => {
          const freshUser: AuthUser = { id: me.id, email: me.email, role: me.role }
          localStorage.setItem('auth_user', JSON.stringify(freshUser))
          setUser(freshUser)
        })
        .catch(() => {
          removeToken()
          localStorage.removeItem('auth_user')
          OpenAPI.TOKEN = undefined
          setTokenState(null)
          setUser(null)
        })
      return
    }
    if (stored) {
      // Expired/malformed token → clear it so we don't render a logged-in
      // shell that can only 401.
      removeToken()
      localStorage.removeItem('auth_user')
    }
    setIsInitialized(true)
  }, [])

  const login = useCallback((newToken: string, newUser?: AuthUser) => {
    setToken(newToken)
    OpenAPI.TOKEN = newToken
    setTokenState(newToken)
    if (newUser) {
      localStorage.setItem('auth_user', JSON.stringify(newUser))
      setUser(newUser)
    }
  }, [])

  const logout = useCallback(() => {
    removeToken()
    localStorage.removeItem('auth_user')
    OpenAPI.TOKEN = undefined
    setTokenState(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: token !== null,
        isInitialized,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
